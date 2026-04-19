from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
from alpaca.data import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

from bot.config import (
    BAR_LIMIT,
    DAILY_LOOKBACK_DAYS,
    HISTORY_MONTHS,
    MIN_BARS_AFTER_FETCH,
    MIN_BARS_HISTORY,
    SYMBOL,
)


def fetch_bars(
    api_key: str,
    secret_key: str,
    symbol: str = SYMBOL,
    limit: int = BAR_LIMIT,
) -> pd.DataFrame:
    """Fetch recent closed OHLCV bars for *symbol* from Alpaca (Phase 1 live mode).

    Uses a start date anchored ``limit`` minutes ago so the request returns a
    full historical window regardless of account tier. The last
    (still-forming) bar is dropped before returning.

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume.
        Rows are sorted ascending by UTC timestamp.

    Raises:
        ValueError: if fewer than MIN_BARS_AFTER_FETCH rows remain after
                    preprocessing.
    """
    start = datetime.now(tz=timezone.utc) - timedelta(minutes=limit + 1)
    df = _fetch(
        api_key=api_key,
        secret_key=secret_key,
        symbol=symbol,
        timeframe=TimeFrame.Minute,
        start=start,
        limit=limit,
    )

    # Drop the last incomplete (still-forming) bar
    df = df.iloc[:-1].copy()

    if len(df) < MIN_BARS_AFTER_FETCH:
        raise ValueError(
            f"Insufficient bars after preprocessing: "
            f"expected >= {MIN_BARS_AFTER_FETCH}, got {len(df)}. "
            f"Increase BAR_LIMIT in config.py."
        )

    return df


def fetch_bars_range(
    api_key: str,
    secret_key: str,
    symbol: str = SYMBOL,
    timeframe: TimeFrame = TimeFrame.Hour,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> pd.DataFrame:
    """Fetch historical OHLCV bars over a date range for ML training.

    Supports any Alpaca TimeFrame value including TimeFrame.Hour (default)
    and TimeFrame.Day (Phase 4 daily bars).  Defaults to the past
    HISTORY_MONTHS months at hourly granularity when start/end are not
    provided.

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume.
        Rows are sorted ascending by UTC timestamp, deduplicated.

    Raises:
        ValueError: if fewer than MIN_BARS_HISTORY rows are returned.
    """
    if end is None:
        end = datetime.now(tz=timezone.utc)
    if start is None:
        start = end - timedelta(days=30 * HISTORY_MONTHS)

    df = _fetch(
        api_key=api_key,
        secret_key=secret_key,
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
    )

    if len(df) < MIN_BARS_HISTORY:
        raise ValueError(
            f"Insufficient historical bars: expected >= {MIN_BARS_HISTORY}, "
            f"got {len(df)}. Widen the date range or increase HISTORY_MONTHS in config.py."
        )

    return df


def fetch_daily_bars(
    api_key: str,
    secret_key: str,
    symbol: str = SYMBOL,
    days_back: int = DAILY_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """Fetch daily OHLCV bars with a lookback anchored to today.

    Convenience wrapper around ``fetch_bars_range`` for the Phase 4
    daily-resolution pipeline.  Returns approximately ``days_back``
    calendar days of daily bars, with the last (potentially incomplete)
    bar dropped.

    Args:
        api_key:    Alpaca API key.
        secret_key: Alpaca secret key.
        symbol:     Crypto pair symbol (default: SYMBOL from config).
        days_back:  Number of calendar days to look back from today
                    (default: DAILY_LOOKBACK_DAYS from config, ~2 years).

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume.
        Rows are sorted ascending by UTC timestamp.

    Raises:
        ValueError: if fewer than MIN_BARS_HISTORY rows are returned.
    """
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days_back)

    df = fetch_bars_range(
        api_key=api_key,
        secret_key=secret_key,
        symbol=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )

    # Drop the last (potentially incomplete) bar — same convention as fetch_bars
    df = df.iloc[:-1].copy().reset_index(drop=True)

    return df


def _fetch(
    api_key: str,
    secret_key: str,
    symbol: str,
    timeframe: TimeFrame,
    start: datetime,
    end: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Internal: fetch, normalize, and sort bars from the Alpaca API."""
    client = CryptoHistoricalDataClient(api_key=api_key, secret_key=secret_key)

    request = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
    )
    bars = client.get_crypto_bars(request)
    df = bars.df  # MultiIndex (symbol, timestamp)

    # Flatten MultiIndex produced by alpaca-py
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level="symbol").reset_index()
    else:
        df = df.reset_index()

    # Keep only the required columns
    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()

    # Cast numeric columns to float64
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype("float64")

    # Normalize timestamps to UTC-aware datetimes
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

    # Sort ascending and deduplicate — do not rely on API ordering
    df = df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)

    return df
