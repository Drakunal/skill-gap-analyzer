# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.logger import logger


class Settings(BaseSettings):
    # --- Generic Fields ---
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # --- Gemini Fields ---
    gemini_api_key: Optional[str] = None
    gemini_model_name: str = "gemini-2.5-flash-lite"

    # --- Cache Limits ---
    max_cv_chars: int = 12000
    max_cached_items: int = 200

    # --- Configuration ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"   # ignore unknown .env keys instead of throwing validation errors
    )


# Initialize settings
settings = Settings()

# Log successful configuration load
logger.info("Settings loaded successfully (env file processed, overrides applied).")
