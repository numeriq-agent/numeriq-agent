from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.config import settings
from app.schemas import ExecutionFill, JudgeDecision


@dataclass
class PaperBroker:
    slippage_bps: float = settings.slippage_bps
    latency_ms: float = 50.0
    positions: dict[str, float] = field(default_factory=dict)
    last_prices: dict[str, float] = field(default_factory=dict)
    pnl: float = 0.0

    def execute(self, decision: JudgeDecision, mark_price: float) -> tuple[ExecutionFill | None, float]:
        if decision.action == "HOLD" or decision.size <= 0:
            return None, 0.0

        side = decision.action
        notional = decision.size * mark_price
        signed_qty = decision.size if side == "BUY" else -decision.size
        self.positions[decision.symbol] = self.positions.get(decision.symbol, 0.0) + signed_qty

        slip_multiplier = 1 + (self.slippage_bps / 1e4) * (1 if side == "BUY" else -1)
        fill_price = mark_price * slip_multiplier
        latency = self.latency_ms + random.uniform(-5, 5)

        pnl_delta = 0.0
        if decision.symbol in self.last_prices:
            pnl_delta = (mark_price - self.last_prices[decision.symbol]) * self.positions[decision.symbol]
            self.pnl += pnl_delta

        self.last_prices[decision.symbol] = mark_price
        fill = ExecutionFill(
            timestamp=datetime.now(tz=timezone.utc),
            symbol=decision.symbol,
            action=side,
            price=fill_price,
            size=decision.size,
            slippage_bps=self.slippage_bps,
            latency_ms=latency,
        )
        return fill, pnl_delta
