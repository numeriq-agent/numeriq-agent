from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from agents import AgentMemory, BaseAgent
from app.schemas import FactualFeatures, JudgeDecision, SubjectiveSignals


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass
class JudgeAgent(BaseAgent):
    weights: Dict[str, float] = field(default_factory=lambda: {"factual": 0.6, "subjective": 0.4})
    bias: float = 0.0
    tau_buy: float = 0.3
    tau_sell: float = -0.3
    k: float = 1.0
    vol_target: float = 0.02
    min_size: float = 0.0
    max_size: float = 1.0

    def __init__(self, **kwargs):
        super().__init__(name="judge-agent", tool=self._tool, memory=AgentMemory())
        for key, value in kwargs.items():
            setattr(self, key, value)

    def score_factual(self, factual: FactualFeatures) -> float:
        feats = factual.features
        rsi = feats.get("rsi_14", 50.0)
        momentum = feats.get("mom_20d", 0.0)
        vol = feats.get("rolling_vol_20d", 0.02)
        volume_z = feats.get("volume_zscore_20d", 0.0)
        rsi_component = (50.0 - rsi) / 50.0  # oversold positive
        momentum_component = clamp(momentum * 5, -1.0, 1.0)
        vol_component = clamp((0.02 - vol) / 0.02, -1.0, 1.0)
        volume_component = clamp(volume_z / 3.0, -1.0, 1.0)
        return clamp(0.4 * rsi_component + 0.4 * momentum_component + 0.2 * volume_component + 0.1 * vol_component, -1.0, 1.0)

    def score_subjective(self, subjective: SubjectiveSignals) -> float:
        sigs = subjective.signals
        sentiment = sigs.get("news_sentiment", 0.0)
        social = sigs.get("social_velocity_z", 0.0)
        headline = sigs.get("headline_sentiment", 0.0)
        search = sigs.get("search_trend_z", 0.0)
        combined = 0.5 * sentiment + 0.2 * headline + 0.2 * clamp(social / 3.0, -1.0, 1.0) + 0.1 * clamp(search / 3.0, -1.0, 1.0)
        return clamp(combined, -1.0, 1.0)

    def _tool(self, factual: FactualFeatures, subjective: SubjectiveSignals) -> JudgeDecision:
        factual_score = self.score_factual(factual)
        subjective_score = self.score_subjective(subjective)
        intent = self.weights["factual"] * factual_score + self.weights["subjective"] * subjective_score + self.bias
        action = "HOLD"
        if intent > self.tau_buy:
            action = "BUY"
        elif intent < self.tau_sell:
            action = "SELL"
        realized_vol = max(factual.features.get("rolling_vol_20d", self.vol_target), 1e-6)
        size = clamp(self.k * intent / realized_vol, self.min_size, self.max_size)
        confidence = clamp(abs(intent), 0.0, 1.0)
        return JudgeDecision(
            timestamp=factual.timestamp,
            symbol=factual.symbol,
            action=action,
            size=abs(size),
            confidence=confidence,
            rationale=[
                f"factual_score={factual_score:.2f}",
                f"subjective_score={subjective_score:.2f}",
                f"intent={intent:.2f}",
            ],
            guardrails_applied=[],
        )

    def run(self, factual: FactualFeatures, subjective: SubjectiveSignals) -> JudgeDecision:
        return super().run(factual=factual, subjective=subjective)
