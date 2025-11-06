from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.schemas import JudgeDecision
from app.utils.time_windows import is_regular_trading_hours


@dataclass
class RiskContext:
    timestamp: datetime
    symbol: str
    current_position: float
    cumulative_pnl: float


class RiskManager:
    """Implements guardrails for trading decisions."""

    def __init__(self, max_position: float = settings.max_position, max_daily_loss: float = settings.max_daily_loss):
        self.max_position = max_position
        self.max_daily_loss = max_daily_loss

    def evaluate(self, decision: JudgeDecision, context: RiskContext) -> JudgeDecision:
        guardrails: list[str] = []

        if not is_regular_trading_hours(context.timestamp):
            guardrails.append("market_closed")

        projected_position = context.current_position
        if decision.action == "BUY":
            projected_position += decision.size
        elif decision.action == "SELL":
            projected_position -= decision.size

        if abs(projected_position) > self.max_position:
            guardrails.append("max_position_exceeded")

        if context.cumulative_pnl < -abs(self.max_daily_loss):
            guardrails.append("max_daily_loss")

        if guardrails:
            return JudgeDecision(
                timestamp=decision.timestamp,
                symbol=decision.symbol,
                action="HOLD",
                size=0.0,
                confidence=decision.confidence,
                rationale=decision.rationale + ["Guardrail override"],
                guardrails_applied=guardrails,
            )

        return decision
