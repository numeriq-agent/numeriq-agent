from functools import lru_cache
from typing import List

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    symbols: List[str] = Field(default_factory=lambda: ["AAPL"], alias="SYMBOLS")
    interval_seconds: int = Field(60, alias="INTERVAL_SECONDS")
    timezone_et: str = Field("America/New_York", alias="TIMEZONE_ET")
    news_api_key: str = Field("", alias="NEWS_API_KEY")
    social_api_key: str = Field("", alias="SOCIAL_API_KEY")
    max_position: int = Field(1000, alias="MAX_POSITION")
    max_daily_loss: float = Field(2500.0, alias="MAX_DAILY_LOSS")
    slippage_bps: float = Field(5.0, alias="SLIPPAGE_BPS")
    database_url: str = Field("sqlite:///./data/paper_trades.db", alias="DATABASE_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    environment: str = Field("local", alias="ENVIRONMENT")

    @field_validator("symbols", mode="before")
    @classmethod
    def _parse_symbols(cls, value: List[str] | str) -> List[str]:
        if isinstance(value, str):
            return [item.strip().upper() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:  # pragma: no cover - configuration errors should surface quickly
        raise RuntimeError("Invalid configuration") from exc


settings = get_settings()
