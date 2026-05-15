from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

import logging
logger = logging.getLogger(__name__)

from Backend.core.logging_config import setup_logging
from Backend.database.connection import connect_db, close_db
from Backend.database.redis_connection import connect_redis, close_redis

from Backend.routes import users, sessions, conversations, analytics, chat
from Backend.services.text_analyser import get_sentiment_analyzer

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Connecting to MongoDB Database...")
    await connect_db()
    logger.info("Successfully connected to MongoDB Database.")
    logger.info("Connecting to Redis Cache...")
    await connect_redis()
    logger.info("Successfully connected to Redis Cache.")

    # Pre-load text analyzer model on startup
    logger.info("Loading text sentiment analyzer...")
    get_sentiment_analyzer()
    logger.info("Text analyzer loaded successfully")

    yield

    await close_db()
    await close_redis()

app = FastAPI(title="SereneAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


