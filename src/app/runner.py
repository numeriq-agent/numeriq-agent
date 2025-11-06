from __future__ import annotations

import time
from datetime import datetime

import typer

from app.config import settings
from app.telemetry import telemetry
from pipelines.orchestrator import MarketMindOrchestrator
from services.execution import PaperBroker
from services.feature_store import FeatureStore
from services.market_data import MockMarketDataProvider
from services.news_data import MockNewsProvider
from services.risk import RiskManager
from services.sentiment import RuleBasedSentiment
from agents.factual_agent import FactualAgent
from agents.subjective_agent import SubjectiveAgent
from agents.judge_agent import JudgeAgent
from pipelines.backtest import run_backtest

app = typer.Typer(add_completion=False, help="Market-Mind runner CLI.")


def build_orchestrator() -> MarketMindOrchestrator:
    market_provider = MockMarketDataProvider()
    feature_store = FeatureStore()
    factual_agent = FactualAgent(provider=market_provider, feature_store=feature_store)

    news_provider = MockNewsProvider()
    sentiment = RuleBasedSentiment()
    subjective_agent = SubjectiveAgent(provider=news_provider, sentiment_model=sentiment)

    judge_agent = JudgeAgent()
    risk_manager = RiskManager()
    broker = PaperBroker()

    return MarketMindOrchestrator(
        factual_agent=factual_agent,
        subjective_agent=subjective_agent,
        judge_agent=judge_agent,
        risk_manager=risk_manager,
        broker=broker,
    )


@app.command()
def live(symbol: str = typer.Option("AAPL"), interval: int = typer.Option(settings.interval_seconds)):
    """Run the live decision loop with mock providers."""
    orchestrator = build_orchestrator()
    typer.echo(f"Starting live loop for {symbol} at {interval}s intervals")
    try:
        while True:
            decision, fill = orchestrator.step(symbol=symbol)
            typer.echo(f"{decision.timestamp.isoformat()} {symbol} {decision.action} size={decision.size:.2f}")
            if fill:
                typer.echo(f" fill @{fill.price:.2f} latency={fill.latency_ms:.1f}ms")
            time.sleep(interval)
    except KeyboardInterrupt:
        typer.echo("Shutting down...")


@app.command()
def backtest(
    symbol: str = typer.Option("AAPL"),
    start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    end: str = typer.Option(..., help="End date YYYY-MM-DD"),
    step_seconds: int = typer.Option(60),
):
    """Run a simple parity backtest using the orchestrator."""
    orchestrator = build_orchestrator()
    start_ts = datetime.fromisoformat(start)
    end_ts = datetime.fromisoformat(end)
    typer.echo(f"Running backtest for {symbol} from {start_ts.date()} to {end_ts.date()}")
    result = run_backtest(orchestrator, symbol=symbol, start=start_ts, end=end_ts, step_seconds=step_seconds)
    typer.echo(f"Decisions generated: {len(result.decisions)} | Trades: {result.trades}")
    metrics = telemetry.export_metrics()
    typer.echo(f"PnL={metrics['pnl']:.2f} Sharpe={metrics['sharpe_30d']:.2f} DD={metrics['max_drawdown']:.2f}")


def main():
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
