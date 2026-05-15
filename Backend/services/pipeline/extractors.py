from Backend.services.pipeline.interfaces import IContextExtractor
from typing import Any, Dict
import base64
from ml_models.CNNModel.cnnmodel import predict_emotion_from_bytes
from Backend.services.text_analyser import analyze_text_sentiment

import logging

logger = logging.getLogger(__name__)

class ImageEmotionExtractor(IContextExtractor):
    async def extract(self, request: Any) -> Dict[str, Any]:
        final_sentiment = getattr(request, "sentiment", "neutral")
        image_data = getattr(request, "image", None)
        
        if image_data:
            logger.info("Camera is ENABLED by the user.")
            try:
                if "," in image_data:
                    image_data = image_data.split(",")[1]

                image_bytes = base64.b64decode(image_data)
                predicted_emotion = predict_emotion_from_bytes(image_bytes)
                if predicted_emotion != "None":
                    logger.info(f"CNN discovered emotion: {predicted_emotion}")
                    final_sentiment = predicted_emotion
            except Exception as e:
                logger.error(f"Failed to extract emotion from image: {e}")
        else:
            logger.info("Camera is DISABLED by the user.")
                
        return {"face_sentiment": final_sentiment}

class TextEmotionExtractor(IContextExtractor):
    async def extract(self, request: Any) -> Dict[str, Any]:
        message = getattr(request, "message", "")
        text_sentiment = analyze_text_sentiment(message)
        return {"text_sentiment": text_sentiment}

class UserInputExtractor(IContextExtractor):
    async def extract(self, request: Any) -> Dict[str, Any]:
        message = getattr(request, "message", "")
        dropout_risk = getattr(request, "dropout_risk", False)
        user_id = getattr(request, "user_id", "")
        return {"message": message, "dropout_risk": dropout_risk, "user_id": user_id}
