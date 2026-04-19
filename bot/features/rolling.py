import pandas as pd

from bot.config import (
    DAILY_REGIME_VOL_WINDOW,
    DAILY_TREND_SLOPE_WINDOW,
    MIN_BARS_AFTER_FEATURES,
    ROLLING_WINDOW,
)

_FEATURE_COLS = ["rolling_mean", "rolling_std", "zscore", "return"]
_EXTENDED_COLS = [
    "return_lag1",
    "return_lag2",
    "return_lag3",
    "momentum_12h",
    "volume_zscore_20",
]


def compute_features(
    df: pd.DataFrame,
    extended: bool = False,
    regime: bool = False,
    timeframe: str = "hourly",
) -> pd.DataFrame:
    """Add rolling statistics and drop warm-up (NaN) rows.

    Derived columns added (always):
        rolling_mean  — rolling mean of close over ROLLING_WINDOW bars
        rolling_std   — rolling std of close over ROLLING_WINDOW bars
        zscore        — (close - rolling_mean) / rolling_std
        return        — bar-over-bar fractional return on close

    Additional columns when extended=True:
        return_lag1   — return shifted by 1 bar
        return_lag2   — return shifted by 2 bars
        return_lag3   — return shifted by 3 bars
        momentum_12h  — sum of last 12 bar returns (half-day trend, hourly)
                        OR sum of last 5 bar returns (1-week trend, daily)
        volume_zscore_20 — z-score of volume over 20-bar rolling window
                           (hourly) OR 5-bar rolling window (daily)

    Additional columns when regime=True (requires extended=True):
        vol_percentile       — 0/1/2 bucket of current vol vs. last N-bar history
                               (252 bars hourly, 60 bars daily)
        trend_slope          — OLS slope of close over N bars, normalised by rolling_std
                               (24 bars hourly, 10 bars daily)
        atr_normalized_return — bar return / ATR: how big was this move relative to normal?

    Args:
        df:        Raw OHLCV DataFrame.
        extended:  Include momentum and lag features.
        regime:    Include regime features (requires extended=True).
        timeframe: ``"hourly"`` (default) or ``"daily"`` — controls lookback
                   window scaling for momentum, volume z-score, and regime features.

    All features use only data at or before bar t (no future leakage).

    Returns:
        DataFrame with feature columns, NaN warm-up rows removed.

    Raises:
        ValueError: if fewer than MIN_BARS_AFTER_FEATURES rows remain.
    """
    df = df.copy()

    df["rolling_mean"] = df["close"].rolling(window=ROLLING_WINDOW).mean()
    df["rolling_std"] = df["close"].rolling(window=ROLLING_WINDOW).std()
    df["zscore"] = (df["close"] - df["rolling_mean"]) / df["rolling_std"]
    df["return"] = (df["close"] - df["close"].shift(1)) / df["close"].shift(1)

    feature_cols = list(_FEATURE_COLS)

    if extended:
        # Select momentum and volume z-score window sizes based on timeframe
        momentum_window = 5 if timeframe == "daily" else 12
        vol_zscore_window = 5 if timeframe == "daily" else ROLLING_WINDOW

        df["return_lag1"] = df["return"].shift(1)
        df["return_lag2"] = df["return"].shift(2)
        df["return_lag3"] = df["return"].shift(3)
        df["momentum_12h"] = df["return"].rolling(window=momentum_window).sum()
        vol_mean = df["volume"].rolling(window=vol_zscore_window).mean()
        vol_std = df["volume"].rolling(window=vol_zscore_window).std()
        df["volume_zscore_20"] = (df["volume"] - vol_mean) / vol_std
        feature_cols = feature_cols + list(_EXTENDED_COLS)

    # Drop warm-up rows where any feature is undefined
    df = df.dropna(subset=feature_cols).reset_index(drop=True)

    if len(df) < MIN_BARS_AFTER_FEATURES:
        raise ValueError(
            f"Insufficient bars after feature computation: "
            f"expected >= {MIN_BARS_AFTER_FEATURES}, got {len(df)}. "
            f"Increase BAR_LIMIT or reduce ROLLING_WINDOW in config.py."
        )

    # ── Phase 3: Regime features ─────────────────────────────────────────────
    # Regime features describe the market's current "state" (calm vs volatile,
    # trending vs choppy).  They require extended=True because they depend on
    # rolling_std and return, which are only guaranteed complete in extended mode.
    if regime:
        # Import here to avoid a module-level circular dependency
        from bot.features.regime import compute_regime_features  # noqa: PLC0415
        df = compute_regime_features(df, timeframe=timeframe)

    return df
