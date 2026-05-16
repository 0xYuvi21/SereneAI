from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

# Resolve the .env file relative to this file's location (Backend/core/config.py -> Backend/.env)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    database_name: str = Field(default="sereneai_db")
    redis_url: str = Field(default="redis://localhost:6379")
    secret_key: str
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    groq_api_key: str
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    hf_token: str

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

settings = Settings()

def get_settings():
    return settings

