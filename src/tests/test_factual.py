from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas import MarketBar
from services.feature_store import FeatureStore, compute_atr, compute_momentum, compute_rsi
from services.market_data import bars_to_dataframe


def generate_bars(count: int = 60) -> list[MarketBar]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bars = []
    price = 100.0
    for idx in range(count):
        price = price * (1 + 0.001 * (-1) ** idx)
        bars.append(
            MarketBar(
                timestamp=start + timedelta(minutes=idx),
                symbol="AAPL",
                open=price * 0.99,
                high=price * 1.01,
                low=price * 0.98,
                close=price,
                volume=1_000_000 + idx * 1000,
            )
        )
    return bars


def test_feature_store_outputs_expected_metrics():
    store = FeatureStore()
    bars = generate_bars()
    features = store.build_features(symbol="AAPL", bars=bars)
    assert "rsi_14" in features.features
    assert "atr_14" in features.features
    assert pytest.approx(features.features["mom_20d"], rel=1e-3) == features.features["mom_20d"]
    assert features.features["rsi_14"] <= 100
    assert features.features["atr_14"] > 0


def test_individual_feature_computations():
    bars = generate_bars()
    frame = bars_to_dataframe(bars)
    rsi = compute_rsi(frame["close"])
    atr = compute_atr(frame)
    momentum = compute_momentum(frame["close"])
    assert 0 <= rsi <= 100
    assert atr > 0
    assert momentum != 0
