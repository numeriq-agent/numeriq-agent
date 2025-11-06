from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from app.schemas import ExecutionFill, JudgeDecision
from pipelines.orchestrator import MarketMindOrchestrator


@dataclass
class BacktestResult:
    decisions: List[JudgeDecision]
    fills: List[ExecutionFill]

    @property
    def trades(self) -> int:
        return len(self.fills)


def run_backtest(
    orchestrator: MarketMindOrchestrator,
    symbol: str,
    start: datetime,
    end: datetime,
    step_seconds: int = 60,
) -> BacktestResult:
    decisions: List[JudgeDecision] = []
    fills: List[ExecutionFill] = []
    cursor = start
    while cursor <= end:
        decision, fill = orchestrator.step(symbol=symbol)
        decisions.append(decision)
        if fill:
            fills.append(fill)
        cursor = cursor + timedelta(seconds=step_seconds)
    return BacktestResult(decisions=decisions, fills=fills)
