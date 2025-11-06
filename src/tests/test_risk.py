from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import JudgeDecision
from services.risk import RiskContext, RiskManager


def test_market_closed_guardrail():
    manager = RiskManager(max_position=10, max_daily_loss=1000)
    decision = JudgeDecision(
        timestamp=datetime.now(tz=timezone.utc),
        symbol="AAPL",
        action="BUY",
        size=5,
        confidence=0.8,
        rationale=[],
        guardrails_applied=[],
    )
    context = RiskContext(
        timestamp=datetime(2024, 1, 6, 12, tzinfo=timezone.utc),  # Saturday
        symbol="AAPL",
        current_position=0,
        cumulative_pnl=0,
    )
    guarded = manager.evaluate(decision, context=context)
    assert guarded.action == "HOLD"
    assert "market_closed" in guarded.guardrails_applied


def test_max_loss_guardrail():
    manager = RiskManager(max_position=10, max_daily_loss=100)
    decision = JudgeDecision(
        timestamp=datetime.now(tz=timezone.utc),
        symbol="AAPL",
        action="SELL",
        size=5,
        confidence=0.6,
        rationale=[],
        guardrails_applied=[],
    )
    context = RiskContext(
        timestamp=datetime(2024, 1, 2, 15, tzinfo=timezone.utc),
        symbol="AAPL",
        current_position=0,
        cumulative_pnl=-150,
    )
    guarded = manager.evaluate(decision, context=context)
    assert guarded.action == "HOLD"
    assert "max_daily_loss" in guarded.guardrails_applied
