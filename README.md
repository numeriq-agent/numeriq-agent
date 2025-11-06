# Numeriq Market-Mind Agent

Numeriq Market-Mind is a reference implementation of a managed trading agent built on the Google Agent Development Kit (Python SDK). The system combines deterministic market features and qualitative sentiment signals, fuses them through a judge agent, enforces risk guardrails, and executes trades in a paper environment with telemetry exposed via FastAPI.

## Architecture

```
          +----------------+       +-------------------+
          |  FactualAgent  |       |  SubjectiveAgent  |
          | (Market data)  |       | (News/Social)     |
          +--------+-------+       +---------+---------+
                   |                         |
                   v                         v
                 features                 signals
                   \                         /
                    \                       /
                     v                     v
                +-------------------------------+
                |           JudgeAgent          |
                |  normalize + fuse + size      |
                +-----------+-------------------+
                            |
                 decision (buy/sell/hold)
                            |
                +-------------------------------+
                |   RiskManager + PaperBroker   |
                | guardrails + simulated fills  |
                +-------------------------------+
                            |
                      telemetry/logs
```

## Quickstart

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Configure environment:
   ```bash
   cp .env.example .env
   ```
   Populate keys (leave empty to use built-in mocks).
3. Run the live loop:
   ```bash
   uv run python -m app.runner live --symbol AAPL
   ```
4. Run a backtest:
   ```bash
   uv run python -m app.runner backtest --symbol AAPL --start 2024-01-01 --end 2024-01-31
   ```
5. Launch the API:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
6. Call endpoints:
   - `GET /health`
   - `POST /decide?symbol=AAPL`
   - `GET /latest?symbol=AAPL`
   - `GET /telem?symbol=AAPL`
   - `GET /metrics`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SYMBOLS` | Tracked tickers (comma-separated). | `AAPL,MSFT` |
| `INTERVAL_SECONDS` | Poll interval for live loop. | `60` |
| `TIMEZONE_ET` | Trading timezone identifier. | `America/New_York` |
| `NEWS_API_KEY` | Optional news provider key. | _empty_ |
| `SOCIAL_API_KEY` | Optional social provider key. | _empty_ |
| `MAX_POSITION` | Max net position size (shares). | `1000` |
| `MAX_DAILY_LOSS` | Daily loss stop in USD. | `2500.0` |
| `SLIPPAGE_BPS` | Simulated execution slippage (bps). | `5.0` |
| `DATABASE_URL` | SQLite path for paper fills. | `sqlite:///./data/paper_trades.db` |
| `LOG_LEVEL` | Structlog logging threshold. | `INFO` |

## Agent Orchestration

- **FactualAgent** pulls mock OHLCV history, derives features (RSI, ATR, momentum, vol, volume z-score, book imbalance proxy).
- **SubjectiveAgent** collects mock news/social signals, enriches them with a rule-based sentiment scorer.
- **JudgeAgent** normalizes both channels, fuses with configurable weights, and emits a decision intent with confidence and position size.
- **RiskManager** applies trading hours, position, and loss guardrails; overrides with HOLD when triggered.
- **PaperBroker** simulates fills with configurable slippage and latency, updating PnL for telemetry.

## Extending Features & Signals

1. Add a new computation in `services/feature_store.py` or `services/news_data.py`.
2. Register the value in the `features` or `signals` dictionaries.
3. Update `JudgeAgent.score_factual` or `score_subjective` to include the new factor.
4. Add unit tests to cover edge cases and normalization.

## Risk Policy Tuning

- Update environment variables (`MAX_POSITION`, `MAX_DAILY_LOSS`) to tighten or relax guardrails.
- Modify `JudgeAgent` weights in `build_orchestrator()` for different factual/subjective emphases:
  ```python
  JudgeAgent(weights={"factual": 0.7, "subjective": 0.3}, tau_buy=0.25, tau_sell=-0.25)
  ```
- Adjust volatility target (`vol_target`) and sizing factor (`k`) to scale exposures to market conditions.

## Telemetry & Metrics

Structured JSON logs capture every decision and fill. Metrics (`PnL`, `Sharpe`, `Max Drawdown`) are exposed through `/metrics` and can be scraped by dashboards. `/telem` returns the latest snapshot paired with the most recent decision.

## Development Workflow

- Format and lint:
  ```bash
  uv run ruff check .
  uv run black .
  ```
- Tests:
  ```bash
  uv run pytest -q
  ```
- Git hooks:
  ```bash
  pre-commit install
  ```

## Docker & Compose

- Build and run the API:
  ```bash
  docker compose up --build
  ```
  This launches the FastAPI service and a background runner container sharing the paper-trading volume.

## License

Released under the Apache License 2.0.
