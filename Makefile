run-live:
	uv run python -m app.runner live --symbol AAPL --interval 60

run-backtest:
	uv run python -m app.runner backtest --symbol AAPL --start 2024-01-01 --end 2024-01-31

api:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest -q
