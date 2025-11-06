from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import SubjectiveSignals
from agents.subjective_agent import SubjectiveAgent
from services.sentiment import RuleBasedSentiment


class StaticNewsProvider:
    def fetch_signals(self, symbol: str) -> SubjectiveSignals:
        return SubjectiveSignals(
            timestamp=datetime.now(tz=timezone.utc),
            symbol=symbol,
            signals={"news_sentiment": 0.5, "social_velocity_z": 1.0},
            notes=["Growth beats expectations"],
        )


def test_subjective_agent_enriches_signals():
    agent = SubjectiveAgent(provider=StaticNewsProvider(), sentiment_model=RuleBasedSentiment())
    result = agent.run(symbol="AAPL")
    assert "headline_sentiment" in result.signals
    assert -1.0 <= result.signals["headline_sentiment"] <= 1.0
