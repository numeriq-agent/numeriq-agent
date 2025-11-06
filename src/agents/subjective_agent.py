from __future__ import annotations

from dataclasses import dataclass

from agents import AgentMemory, BaseAgent
from app.schemas import SubjectiveSignals
from services.news_data import NewsProvider
from services.sentiment import SentimentModel


@dataclass
class SubjectiveAgent(BaseAgent):
    provider: NewsProvider
    sentiment_model: SentimentModel

    def __init__(self, provider: NewsProvider, sentiment_model: SentimentModel):
        self.provider = provider
        self.sentiment_model = sentiment_model
        super().__init__(name="subjective-agent", tool=self._tool, memory=AgentMemory())

    def _tool(self, symbol: str) -> SubjectiveSignals:
        signals = self.provider.fetch_signals(symbol)
        enriched = dict(signals.signals)
        if signals.notes:
            enriched["headline_sentiment"] = self.sentiment_model.score(" ".join(signals.notes))
        signals.signals = enriched
        return signals

    def run(self, symbol: str) -> SubjectiveSignals:
        return super().run(symbol=symbol)
