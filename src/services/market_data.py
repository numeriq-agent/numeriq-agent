from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Protocol

import pandas as pd

from app.schemas import MarketBar


class MarketDataProvider(Protocol):
    def get_bars(self, symbol: str, lookback: int) -> list[MarketBar]:
        ...


@dataclass
class MockMarketDataProvider(MarketDataProvider):
    seed: int = 42

    def __post_init__(self) -> None:
        random.seed(self.seed)

    def get_bars(self, symbol: str, lookback: int) -> list[MarketBar]:
        end = datetime.now(tz=timezone.utc)
        start_price = 100.0 + random.random() * 5
        prices = [start_price]
        volumes = [1_000_000.0]
        for _ in range(lookback - 1):
            change = random.gauss(0, 1)
            price = max(1.0, prices[-1] * (1 + change / 100))
            prices.append(price)
            volumes.append(max(100_000.0, volumes[-1] * (1 + random.gauss(0, 0.01))))

        timestamps = [
            end - timedelta(minutes=i) for i in reversed(range(lookback))
        ]  # 1-minute spacing for mock
        bars: list[MarketBar] = []
        for ts, price, vol in zip(timestamps, prices, volumes, strict=False):
            high = price * (1 + abs(random.gauss(0, 0.003)))
            low = price * (1 - abs(random.gauss(0, 0.003)))
            bar = MarketBar(
                timestamp=ts,
                symbol=symbol,
                open=price * (1 - random.uniform(-0.001, 0.001)),
                high=high,
                low=low,
                close=price,
                volume=vol,
            )
            bars.append(bar)
        return bars


def bars_to_dataframe(bars: Iterable[MarketBar]) -> pd.DataFrame:
    frame = pd.DataFrame([bar.model_dump() for bar in bars])
    frame.set_index("timestamp", inplace=True)
    return frame.sort_index()
