from __future__ import annotations

import sqlite3
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque

import numpy as np
import structlog

from app.config import settings
from app.schemas import ExecutionFill, JudgeDecision, TelemetrySnapshot

LOG = structlog.get_logger("market_mind")

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)


class TelemetryStore:
    """Tracks decisions, fills, and derived metrics."""

    def __init__(self, database_url: str):
        self.database_url = database_url.replace("sqlite:///", "")
        Path(self.database_url).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.pnl_history: Deque[float] = deque(maxlen=512)
        self.timestamps: Deque[datetime] = deque(maxlen=512)
        self.decisions: Deque[JudgeDecision] = deque(maxlen=32)

    def _init_db(self) -> None:
        with sqlite3.connect(self.database_url) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    size REAL NOT NULL,
                    slippage_bps REAL NOT NULL,
                    latency_ms REAL NOT NULL
                )
                """
            )
            conn.commit()

    def record_decision(self, decision: JudgeDecision) -> None:
        LOG.info("decision", symbol=decision.symbol, action=decision.action, size=decision.size)
        self.decisions.append(decision)

    def record_fill(self, fill: ExecutionFill, pnl_delta: float) -> None:
        LOG.info(
            "fill",
            symbol=fill.symbol,
            action=fill.action,
            price=fill.price,
            size=fill.size,
            slippage_bps=fill.slippage_bps,
            latency_ms=fill.latency_ms,
        )
        with sqlite3.connect(self.database_url) as conn:
            conn.execute(
                "INSERT INTO fills (ts, symbol, side, price, size, slippage_bps, latency_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    fill.timestamp.isoformat(),
                    fill.symbol,
                    fill.action,
                    fill.price,
                    fill.size,
                    fill.slippage_bps,
                    fill.latency_ms,
                ),
            )
            conn.commit()
        self._update_pnl(fill.timestamp, pnl_delta)

    def _update_pnl(self, timestamp: datetime, pnl_delta: float) -> None:
        cumulative = (self.pnl_history[-1] if self.pnl_history else 0.0) + pnl_delta
        self.pnl_history.append(cumulative)
        self.timestamps.append(timestamp)

    def compute_sharpe(self) -> float:
        if len(self.pnl_history) < 5:
            return 0.0
        returns = np.diff(np.array(self.pnl_history))
        if returns.std() == 0:
            return 0.0
        return float(np.sqrt(252) * returns.mean() / returns.std())

    def compute_drawdown(self) -> float:
        if not self.pnl_history:
            return 0.0
        pnl = np.array(self.pnl_history)
        running_max = np.maximum.accumulate(pnl)
        drawdowns = (pnl - running_max).min()
        return float(drawdowns)

    def latest_snapshot(self, symbol: str) -> TelemetrySnapshot:
        decision = self.decisions[-1] if self.decisions else None
        ts = datetime.now(tz=timezone.utc)
        pnl = self.pnl_history[-1] if self.pnl_history else 0.0
        return TelemetrySnapshot(
            timestamp=ts,
            symbol=symbol,
            pnl=pnl,
            sharpe_30d=self.compute_sharpe(),
            max_drawdown=self.compute_drawdown(),
            decision=decision,
        )

    def export_metrics(self) -> dict[str, float]:
        snapshot = self.latest_snapshot(symbol=settings.symbols[0])
        return {
            "pnl": snapshot.pnl,
            "sharpe_30d": snapshot.sharpe_30d,
            "max_drawdown": snapshot.max_drawdown,
        }


telemetry = TelemetryStore(database_url=settings.database_url)


def timed_op(operation: str):
    """Decorator to measure latency of an operation."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            latency = (time.perf_counter() - start) * 1000.0
            LOG.info("latency", operation=operation, latency_ms=latency)
            return result, latency

        return wrapper

    return decorator
