from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.schemas import SubjectiveSignals


class NewsProvider(Protocol):
    def fetch_signals(self, symbol: str) -> SubjectiveSignals:
        ...


@dataclass
class MockNewsProvider(NewsProvider):
    seed: int = 123

    def __post_init__(self) -> None:
        random.seed(self.seed)

    def fetch_signals(self, symbol: str) -> SubjectiveSignals:
        score = random.uniform(-1.0, 1.0)
        notes = [f"Mock headline sentiment {score:.2f} for {symbol}"]
        signals = {
            "news_sentiment": score,
            "social_velocity_z": random.uniform(-1.5, 1.5),
            "search_trend_z": random.uniform(-1.0, 1.0),
        }
        return SubjectiveSignals(
            timestamp=datetime.now(tz=timezone.utc),
            symbol=symbol,
            signals=signals,
            notes=notes,
        )
