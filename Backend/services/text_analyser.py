import logging
from transformers import pipeline
from Backend.core.config import get_settings


setting = get_settings()
logger = logging.getLogger(__name__)

# Simple sentiment pipeline
_sentiment_analyzer = None

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = pipeline(

            "sentiment-analysis", 
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            token=setting.hf_token

    )
    return _sentiment_analyzer

def analyze_text_sentiment(text: str) -> str:
    try:
        analyzer = get_sentiment_analyzer()
        result = analyzer(text)[0]
        label = result['label'].lower()
        score = result.get('score', 0.0)
        preview = text[:60].replace('\n', ' ')
        logger.info("Text sentiment detected | label=%s | confidence=%.4f | input='%s...'", label, score, preview)
        return label
    except Exception as e:
        logger.error("Error analyzing text sentiment: %s", e)
        return "neutral"
