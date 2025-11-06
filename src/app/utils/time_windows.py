from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import pandas as pd
from dateutil import tz

from app.config import settings


def is_regular_trading_hours(timestamp: datetime) -> bool:
    """Return True if timestamp (UTC) is within U.S. equity regular trading hours."""
    eastern = tz.gettz(settings.timezone_et)
    ts_local = timestamp.astimezone(eastern)
    open_time = time(hour=9, minute=30)
    close_time = time(hour=16, minute=0)
    return open_time <= ts_local.time() <= close_time and ts_local.weekday() < 5


def rolling_window(series: pd.Series, window: int) -> pd.Series:
    """Compute rolling mean for convenience."""
    return series.rolling(window=window, min_periods=1).mean()


def floor_to_interval(timestamp: datetime, seconds: int) -> datetime:
    epoch = datetime.fromtimestamp(0, tz=timezone.utc)
    delta = timestamp - epoch
    floored = int(delta.total_seconds() // seconds) * seconds
    return epoch + timedelta(seconds=floored)
