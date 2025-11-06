from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import FactualFeatures, SubjectiveSignals
from agents.judge_agent import JudgeAgent


def make_factual(rsi: float, momentum: float, vol: float) -> FactualFeatures:
    return FactualFeatures(
        timestamp=datetime.now(tz=timezone.utc),
        symbol="AAPL",
        features={
            "rsi_14": rsi,
            "mom_20d": momentum,
            "rolling_vol_20d": vol,
            "volume_zscore_20d": 1.0,
            "last_close": 100.0,
        },
    )


def make_subjective(sentiment: float) -> SubjectiveSignals:
    return SubjectiveSignals(
        timestamp=datetime.now(tz=timezone.utc),
        symbol="AAPL",
        signals={"news_sentiment": sentiment, "social_velocity_z": sentiment},
    )


def test_judge_agent_buy_signal():
    judge = JudgeAgent()
    factual = make_factual(rsi=30, momentum=0.05, vol=0.01)
    subjective = make_subjective(sentiment=0.8)
    decision = judge.run(factual=factual, subjective=subjective)
    assert decision.action == "BUY"
    assert 0 <= decision.size <= judge.max_size


def test_judge_agent_sell_signal():
    judge = JudgeAgent()
    factual = make_factual(rsi=80, momentum=-0.05, vol=0.01)
    subjective = make_subjective(sentiment=-0.8)
    decision = judge.run(factual=factual, subjective=subjective)
    assert decision.action == "SELL"
