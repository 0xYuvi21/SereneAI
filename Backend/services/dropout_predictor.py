"""
Dropout Risk Predictor
======================
Loads the trained PyTorch neural-network model and StandardScaler from disk
and provides a single async function `predict_dropout_risk` that:

  1. Gathers all required features from MongoDB for the just-ended session.
  2. Scales them with the saved scaler.
  3. Runs inference with the trained model.
  4. Returns a float probability (0-1) and a label ("Low" | "Medium" | "High").

Feature vector (must match training order exactly):
  [session_frequency, session_duration, messages_sent,
   days_since_last, start_emotion, end_emotion]

Emotion encoding (matches notebook ordinal encoding):
  happy    -> 1
  surprise -> 2
  neutral  -> 3
  fear     -> 4
  sad      -> 5
  angry    -> 6
  disgust  -> 7
  negative -> 8   (catch-all for unknown negative states)
  unknown  -> 3   (default to neutral)
"""

import logging
import joblib
import pickle
import importlib.resources
import torch
from torch import nn
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Model artifacts are loaded via importlib.resources from the local package

# ---------------------------------------------------------------------------
# Model architecture  (must match the architecture used during training)
# ---------------------------------------------------------------------------
class DropoutChurnModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(6, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.model(x)


# ---------------------------------------------------------------------------
# Lazy-load model & scaler once, reuse across requests
# ---------------------------------------------------------------------------
_model: DropoutChurnModel | None = None
_scaler = None


def _load_artifacts():
    global _model, _scaler
    if _model is None:
        model_path = importlib.resources.files("ml_models.Dropout").joinpath("dropout_model.pth")
        m = DropoutChurnModel()
        with model_path.open("rb") as f:
            m.load_state_dict(torch.load(f, map_location="cpu"))
        m.eval()
        _model = m
        logger.info("Dropout model loaded from ml_models.Dropout")
    if _scaler is None:
        scaler_path = importlib.resources.files("ml_models.Dropout").joinpath("scaler.pkl")
        
        with scaler_path.open("rb") as f:
            _scaler = joblib.load(f)
        logger.info("Scaler loaded from ml_models.Dropout")


# ---------------------------------------------------------------------------
# Emotion encoding
# ---------------------------------------------------------------------------
_EMOTION_MAP: dict[str, int] = {
    "happy": 1,
    "surprise": 2,
    "neutral": 3,
    "fear": 4,
    "sad": 5,
    "angry": 6,
    "disgust": 7,
    "negative": 8,
}
_DEFAULT_EMOTION = 3  # neutral


def _encode_emotion(emotion: str | None) -> int:
    if emotion is None:
        return _DEFAULT_EMOTION
    return _EMOTION_MAP.get(emotion.lower().strip(), _DEFAULT_EMOTION)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def predict_dropout_risk(
    session: dict,
    user_id: str,
    db,
) -> tuple[float, str]:
    """
    Predict dropout (churn) risk for a user at the end of a session.

    Parameters
    ----------
    session : dict
        The fully-updated session document (after end_session writes its fields).
    user_id : str
        The user's UUID string.
    db :
        An async MongoDB database handle (from get_database()).

    Returns
    -------
    (probability, label)
        probability – float in [0, 1]
        label       – "Low" | "Medium" | "High"
    """
    _load_artifacts()
    
    end_time = session.get("session_end_time") or datetime.now(timezone.utc)
    
    # 1. session_frequency — total closed sessions for this user in the last 24 hours (including this one)
    session_frequency = await db.sessions.count_documents(
        {
            "user_id": user_id,
            "session_end_time": {
                "$gte": end_time - timedelta(days=1),
                "$lte": end_time
            }
        }
    )

    # 2. session_duration — in minutes (model was trained with minute-scale values)
    raw_duration = session.get("session_duration") or 0.0  # seconds from DB
    session_duration_minutes = raw_duration / 60.0

    # 3. messages_sent — messages in this session
    messages_sent = session.get("messages_sent_count") or 0

    # 4. days_since_last — days since the previous session (0 if first session)
    days_since_last = session.get("days_since_last_session") or 0.0

    # 5 & 6. emotion encoding
    start_emotion = _encode_emotion(session.get("emotion_at_start"))
    end_emotion = _encode_emotion(session.get("emotion_at_end"))

    # Build feature vector  [frequency, duration_min, messages, days, e_start, e_end]
    features = [
        float(session_frequency),
        float(session_duration_minutes),
        float(messages_sent),
        float(days_since_last),
        float(start_emotion),
        float(end_emotion),
    ]

    import numpy as np  # local import – already a dep via scikit-learn
    X = _scaler.transform([features])
    tensor = torch.tensor(X, dtype=torch.float32)

    with torch.inference_mode():
        logit = _model(tensor)
        probability = torch.sigmoid(logit).item()

    # Label thresholds
    if probability >= 0.7:
        label = "High"
    elif probability >= 0.4:
        label = "Medium"
    else:
        label = "Low"

    logger.info(
        "Dropout risk for user %s — prob=%.4f label=%s  features=%s",
        user_id, probability, label, features,
    )
    return probability, label
