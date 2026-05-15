"""
Analytics Service
=================
Provides all computed metrics consumed by the Dashboard:

  get_emotion_trends(user_id)   → timeseries of wellbeing scores per session
  get_dropout_risk(user_id)     → ML-predicted churn risk (or heuristic fallback)
  get_recovery_rate(user_id)    → behavioural recovery metric (formula below)
  get_dashboard_summary(user_id)→ top-stat card data + emotion distribution

Recovery Rate Formula
---------------------
A session is considered a "positive" (recovered) session when any of the
following is true:
  1. emotion_at_end is better than emotion_at_start  (emotion improved)
  2. Both start and end emotions are in the "positive" bucket
  3. The session was engaged (is_active = True  →  7+ messages sent)

  recovery_rate = (positive_sessions / total_sessions_with_data) * 100

The score is bounded to [0, 100] and rounded to one decimal place.
"""

from Backend.database.connection import get_database
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Higher number = more positive emotion.
_EMOTION_VALENCE: dict[str, int] = {
    "happy": 9,
    "surprise": 7,
    "hopeful": 7,
    "calm": 6,
    "neutral": 5,
    "fear": 3,
    "sad": 2,
    "angry": 2,
    "disgust": 1,
    "negative": 1,
    "depressed": 1,
}
_POSITIVE_THRESHOLD = 6  # valence >= 6 is "positive"

_SCORE_MAP: dict[str, int] = {
    "happy": 90, "hopeful": 80, "calm": 75, "surprise": 70,
    "neutral": 50,
    "fear": 35, "sad": 25, "angry": 20, "disgust": 15,
    "negative": 15, "depressed": 10,
}


def _valence(emotion: str | None) -> int:
    if not emotion:
        return _EMOTION_VALENCE["neutral"]
    return _EMOTION_VALENCE.get(emotion.lower().strip(), _EMOTION_VALENCE["neutral"])


def _score(emotion: str | None) -> int:
    if not emotion:
        return _SCORE_MAP["neutral"]
    return _SCORE_MAP.get(emotion.lower().strip(), _SCORE_MAP["neutral"])


def _is_positive_session(session: dict) -> bool:
    """Return True if the session shows a recovery/positive signal."""
    start_v = _valence(session.get("emotion_at_start"))
    end_v = _valence(session.get("emotion_at_end"))
    engaged = session.get("is_active", False)  # True = 7+ messages sent

    # Improved emotion
    if end_v > start_v:
        return True
    # Both already positive
    if start_v >= _POSITIVE_THRESHOLD and end_v >= _POSITIVE_THRESHOLD:
        return True
    # Engaged session with at least a stable (non-negative) end
    if engaged and end_v >= _EMOTION_VALENCE["neutral"]:
        return True
    return False


# ---------------------------------------------------------------------------
# Public Functions
# ---------------------------------------------------------------------------

async def get_emotion_trends(user_id: str):
    db = get_database()
    cursor = db.sessions.find(
        {"user_id": user_id, "session_end_time": {"$ne": None}}
    ).sort("session_start_time", 1).limit(20)

    trends = []
    async for session in cursor:
        start_emotion = session.get("emotion_at_start", "neutral") or "neutral"
        end_emotion = session.get("emotion_at_end")
        date_str = session.get("session_date") or (
            session["session_start_time"].strftime("%Y-%m-%d")
            if session.get("session_start_time") else "N/A"
        )
        # Use end emotion if available, else start emotion, for trend score
        primary_emotion = end_emotion if end_emotion else start_emotion
        trends.append({
            "date": date_str,
            "score": _score(primary_emotion),
            "session_date": date_str,
            "emotion_at_start": start_emotion,
            "emotion_at_end": end_emotion,
        })

    return {"trends": trends}


async def get_dropout_risk(user_id: str):
    """
    Returns the dropout risk for a user based on the most recent
    neural-network prediction stored in the DB.
    Falls back to the session-count heuristic only if no ML score exists yet.
    """
    db = get_database()

    latest_session = await db.sessions.find_one(
        {"user_id": user_id, "session_end_time": {"$ne": None}, "dropout_risk_score": {"$ne": None}},
        sort=[("session_end_time", -1)]
    )

    if latest_session and latest_session.get("dropout_risk_score") is not None:
        probability = latest_session["dropout_risk_score"]
        if probability >= 0.7:
            risk = "High"
        elif probability >= 0.4:
            risk = "Medium"
        else:
            risk = "Low"
        return {"risk_score": risk, "dropout_risk_probability": round(probability, 4)}

    # Fallback heuristic
    count = await db.sessions.count_documents({"user_id": user_id})
    if count < 2:
        risk, probability = "High", 0.9
    elif count < 5:
        risk, probability = "Medium", 0.5
    else:
        risk, probability = "Low", 0.2

    return {"risk_score": risk, "dropout_risk_probability": probability}


async def get_recovery_rate(user_id: str):
    """
    Compute a recovery rate from behavioural session signals.
    See module docstring for the full formula.
    """
    db = get_database()

    # Only analyse completed sessions that have emotion data
    cursor = db.sessions.find(
        {"user_id": user_id, "session_end_time": {"$ne": None}}
    ).sort("session_start_time", -1).limit(30)  # look back up to 30 sessions

    sessions = []
    async for s in cursor:
        sessions.append(s)

    total = len(sessions)
    if total == 0:
        return {
            "rate": 0.0,
            "status": "Insufficient Data",
            "sessions_analysed": 0,
            "positive_sessions": 0,
        }

    positive = sum(1 for s in sessions if _is_positive_session(s))
    rate = round((positive / total) * 100, 1)

    # Trend status: compare first half vs second half of the window
    if total >= 4:
        mid = total // 2
        recent_half = sessions[:mid]    # most recent (list is desc sorted)
        older_half = sessions[mid:]
        recent_rate = sum(1 for s in recent_half if _is_positive_session(s)) / len(recent_half)
        older_rate = sum(1 for s in older_half if _is_positive_session(s)) / len(older_half)
        diff = recent_rate - older_rate
        if diff > 0.1:
            status = "Improving"
        elif diff < -0.1:
            status = "Declining"
        else:
            status = "Stable"
    else:
        status = "Stable" if rate >= 50 else "Declining"

    return {
        "rate": rate,
        "status": status,
        "sessions_analysed": total,
        "positive_sessions": positive,
    }


async def get_dashboard_summary(user_id: str):
    """
    Aggregates top-stat card data and emotion distribution for the dashboard.
    """
    db = get_database()

    # Fetch user doc for counters and streak
    user = await db.users.find_one({"user_id": user_id})
    total_sessions = user.get("total_sessions", 0) if user else 0
    total_messages = user.get("total_messages", 0) if user else 0
    login_streak = user.get("login_streak", 0) if user else 0

    # All completed sessions for this user
    cursor = db.sessions.find({"user_id": user_id, "session_end_time": {"$ne": None}})

    best_duration = None
    best_date = None
    total_duration = 0.0
    completed_count = 0
    emotion_distribution: dict[str, int] = {}
    active_sessions = 0
    days_since_last = None

    async for session in cursor:
        dur = session.get("session_duration") or 0.0
        total_duration += dur
        completed_count += 1

        if best_duration is None or dur > best_duration:
            best_duration = dur
            best_date = session.get("session_date") or (
                session["session_start_time"].strftime("%Y-%m-%d")
                if session.get("session_start_time") else None
            )

        if session.get("is_active"):
            active_sessions += 1

        # Tally emotions from both start and end
        for emo_field in ("emotion_at_start", "emotion_at_end"):
            emo = session.get(emo_field)
            if emo:
                key = emo.lower().strip()
                emotion_distribution[key] = emotion_distribution.get(key, 0) + 1

    # Days since last session
    last_session = await db.sessions.find_one(
        {"user_id": user_id, "session_end_time": {"$ne": None}},
        sort=[("session_end_time", -1)]
    )
    if last_session and last_session.get("session_end_time"):
        end_t = last_session["session_end_time"]
        if end_t.tzinfo is None:
            end_t = end_t.replace(tzinfo=timezone.utc)
        days_since_last = (datetime.now(timezone.utc) - end_t).days

    avg_duration = (total_duration / completed_count) if completed_count > 0 else None

    latest_insights = user.get("latest_insights") if user else None

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "best_session_duration": best_duration,
        "best_session_date": best_date,
        "avg_session_duration": avg_duration,
        "login_streak": login_streak,
        "emotion_distribution": emotion_distribution,
        "active_sessions": active_sessions,
        "days_since_last_session": days_since_last,
        "latest_insights": latest_insights,
    }


async def get_anxiety_trends(user_id: str):
    """
    Returns RAS and TAS anxiety trends over time for the given user.
    """
    db = get_database()
    cursor = db.sessions.find(
        {"user_id": user_id, "session_end_time": {"$ne": None}, "ras_score": {"$exists": True}}
    ).sort("session_end_time", 1).limit(20)

    trends = []
    async for session in cursor:
        date_str = session.get("session_date") or (
            session["session_end_time"].strftime("%Y-%m-%d")
            if session.get("session_end_time") else "N/A"
        )
        trends.append({
            "date": date_str,
            "ras_score": session.get("ras_score", 0),
            "tas_score": session.get("tas_score", 0)
        })

    return {"anxiety_trends": trends}
