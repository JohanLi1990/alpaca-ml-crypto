import pandas as pd

from bot.config import MIN_BARS_AFTER_FEATURES, ROLLING_WINDOW

_FEATURE_COLS = ["rolling_mean", "rolling_std", "zscore", "return"]


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rolling statistics and drop warm-up (NaN) rows.

    Derived columns added:
        rolling_mean  — rolling mean of close over ROLLING_WINDOW bars
        rolling_std   — rolling std of close over ROLLING_WINDOW bars
        zscore        — (close - rolling_mean) / rolling_std
        return        — bar-over-bar fractional return on close

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

    # Drop warm-up rows where any feature is undefined
    df = df.dropna(subset=_FEATURE_COLS).reset_index(drop=True)

    if len(df) < MIN_BARS_AFTER_FEATURES:
        raise ValueError(
            f"Insufficient bars after feature computation: "
            f"expected >= {MIN_BARS_AFTER_FEATURES}, got {len(df)}. "
            f"Increase BAR_LIMIT or reduce ROLLING_WINDOW in config.py."
        )

    return df
