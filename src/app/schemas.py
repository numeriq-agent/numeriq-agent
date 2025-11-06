from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MarketBar(BaseModel):
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class FactualFeatures(BaseModel):
    timestamp: datetime
    symbol: str
    features: dict[str, float] = Field(default_factory=dict)


class SubjectiveSignals(BaseModel):
    timestamp: datetime
    symbol: str
    signals: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class JudgeDecision(BaseModel):
    timestamp: datetime
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    size: float
    confidence: float
    rationale: list[str]
    guardrails_applied: list[str] = Field(default_factory=list)


class ExecutionFill(BaseModel):
    timestamp: datetime
    symbol: str
    action: Literal["BUY", "SELL"]
    price: float
    size: float
    slippage_bps: float
    latency_ms: float


class TelemetrySnapshot(BaseModel):
    timestamp: datetime
    symbol: str
    pnl: float
    sharpe_30d: float
    max_drawdown: float
    decision: JudgeDecision | None = None
