from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.data import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

from bot.config import BAR_LIMIT, MIN_BARS_AFTER_FETCH, SYMBOL


def fetch_bars(
    api_key: str,
    secret_key: str,
    symbol: str = SYMBOL,
    limit: int = BAR_LIMIT,
) -> pd.DataFrame:
    """Fetch recent closed OHLCV bars for *symbol* from Alpaca.

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
    client = CryptoHistoricalDataClient(api_key=api_key, secret_key=secret_key)

    # Anchor to limit minutes ago so the API returns a full window
    start = datetime.now(tz=timezone.utc) - timedelta(minutes=limit + 1)

    request = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=start,
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

    # Sort ascending — do not rely on API ordering
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Drop the last incomplete (still-forming) bar
    df = df.iloc[:-1].copy()

    if len(df) < MIN_BARS_AFTER_FETCH:
        raise ValueError(
            f"Insufficient bars after preprocessing: "
            f"expected >= {MIN_BARS_AFTER_FETCH}, got {len(df)}. "
            f"Increase BAR_LIMIT in config.py."
        )

    return df
