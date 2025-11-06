from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.config import settings
from app.runner import build_orchestrator
from app.schemas import JudgeDecision, TelemetrySnapshot
from app.telemetry import telemetry

app = FastAPI(title="Numeriq Market-Mind Agent", version="0.1.0")

orchestrator = build_orchestrator()
latest_decisions: dict[str, JudgeDecision] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/latest")
def latest(symbol: str = Query(default="AAPL")) -> JudgeDecision:
    if symbol not in latest_decisions:
        raise HTTPException(status_code=404, detail="No decision yet")
    return latest_decisions[symbol]


@app.get("/telem")
def telem(symbol: str = Query(default="AAPL")) -> TelemetrySnapshot:
    return telemetry.latest_snapshot(symbol=symbol)


@app.get("/metrics")
def metrics() -> dict[str, float]:
    return telemetry.export_metrics()


@app.post("/decide")
def decide(symbol: str = Query(default="AAPL")) -> JudgeDecision:
    decision, _ = orchestrator.step(symbol=symbol)
    latest_decisions[symbol] = decision
    return decision
