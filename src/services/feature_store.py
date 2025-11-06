from __future__ import annotations

import numpy as np
import pandas as pd

from app.schemas import FactualFeatures, MarketBar
from services.market_data import bars_to_dataframe


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(window=period, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period, min_periods=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def compute_atr(frame: pd.DataFrame, period: int = 14) -> float:
    high_low = frame["high"] - frame["low"]
    high_close = (frame["high"] - frame["close"].shift(1)).abs()
    low_close = (frame["low"] - frame["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return float(atr.iloc[-1])


def compute_momentum(series: pd.Series, window: int = 20) -> float:
    return float(series.iloc[-1] / series.shift(window).iloc[-1] - 1)


def compute_volatility(series: pd.Series, window: int = 20) -> float:
    return float(series.pct_change().rolling(window=window).std().iloc[-1])


def compute_volume_zscore(series: pd.Series, window: int = 20) -> float:
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std().replace(0, np.nan)
    zscore = (series - rolling_mean) / rolling_std
    return float(zscore.iloc[-1])


def compute_book_imbalance(_: pd.Series) -> float:
    # Placeholder implementation; real system would inspect L2 order book.
    return 0.0


class FeatureStore:
    """Derives deterministic features for the factual agent."""

    def __init__(self) -> None:
        self.required_history = 120

    def build_features(self, symbol: str, bars: list[MarketBar]) -> FactualFeatures:
        frame = bars_to_dataframe(bars)
        if len(frame) < self.required_history:
            raise ValueError("Insufficient history for feature calculation")

        features = {
            "rsi_14": compute_rsi(frame["close"], period=14),
            "atr_14": compute_atr(frame, period=14),
            "mom_20d": compute_momentum(frame["close"], window=20),
            "rolling_vol_20d": compute_volatility(frame["close"], window=20),
            "book_imbalance": compute_book_imbalance(frame["close"]),
            "volume_zscore_20d": compute_volume_zscore(frame["volume"], window=20),
            "last_close": float(frame["close"].iloc[-1]),
        }
        return FactualFeatures(timestamp=frame.index[-1], symbol=symbol, features=features)
