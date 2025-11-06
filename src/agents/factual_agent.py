from __future__ import annotations

from dataclasses import dataclass

from agents import AgentMemory, BaseAgent
from app.schemas import FactualFeatures
from services.feature_store import FeatureStore
from services.market_data import MarketDataProvider


@dataclass
class FactualAgent(BaseAgent):
    provider: MarketDataProvider
    feature_store: FeatureStore
    lookback: int = 120

    def __init__(self, provider: MarketDataProvider, feature_store: FeatureStore, lookback: int = 120):
        self.provider = provider
        self.feature_store = feature_store
        self.lookback = lookback
        super().__init__(name="factual-agent", tool=self._tool, memory=AgentMemory())

    def _tool(self, symbol: str) -> FactualFeatures:
        bars = self.provider.get_bars(symbol=symbol, lookback=self.lookback)
        features = self.feature_store.build_features(symbol=symbol, bars=bars)
        return features

    def run(self, symbol: str) -> FactualFeatures:
        return super().run(symbol=symbol)
