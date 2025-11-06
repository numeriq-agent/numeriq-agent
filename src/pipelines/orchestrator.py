from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from agents.factual_agent import FactualAgent
from agents.judge_agent import JudgeAgent
from agents.subjective_agent import SubjectiveAgent
from app.schemas import ExecutionFill, JudgeDecision
from app.telemetry import telemetry
from services.execution import PaperBroker
from services.risk import RiskContext, RiskManager


@dataclass
class MarketMindOrchestrator:
    factual_agent: FactualAgent
    subjective_agent: SubjectiveAgent
    judge_agent: JudgeAgent
    risk_manager: RiskManager
    broker: PaperBroker

    def step(self, symbol: str) -> tuple[JudgeDecision, Optional[ExecutionFill]]:
        factual = self.factual_agent.run(symbol=symbol)
        subjective = self.subjective_agent.run(symbol=symbol)
        decision = self.judge_agent.run(factual=factual, subjective=subjective)

        context = RiskContext(
            timestamp=factual.timestamp,
            symbol=symbol,
            current_position=self.broker.positions.get(symbol, 0.0),
            cumulative_pnl=self.broker.pnl,
        )
        guarded = self.risk_manager.evaluate(decision, context=context)
        telemetry.record_decision(guarded)

        mark_price = factual.features.get("last_close", 0.0)
        fill = None
        if guarded.action in {"BUY", "SELL"} and guarded.size > 0:
            fill, pnl_delta = self.broker.execute(guarded, mark_price)
            if fill:
                telemetry.record_fill(fill, pnl_delta=pnl_delta)

        return guarded, fill

