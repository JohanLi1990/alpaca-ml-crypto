from __future__ import annotations

import warnings
from typing import Optional, Union

import pandas as pd

from bot.config import ATR_WINDOW

_FEATURE_COLS = [
    "rolling_mean",
    "rolling_std",
    "zscore",
    "return",
    "return_lag1",
    "return_lag2",
    "return_lag3",
    "momentum_12h",
    "volume_zscore_20",
]


def make_labels(
    df: pd.DataFrame,
    lower: Optional[float] = None,
    upper: Optional[float] = None,
    compute_thresholds: bool = False,
) -> Union[
    tuple[pd.DataFrame, pd.Series, float, float],
    tuple[pd.DataFrame, pd.Series],
]:
    """Label each bar with a binary outcome using quantile-based forward returns.

    The forward return at bar t is (close_{t+1} - close_t) / close_t.
    Bars above the upper threshold are labeled 1 (long); bars below the lower
    threshold are labeled 0 (flat). The middle band is excluded entirely.

    The forward_return column is NOT included in the returned X.

    Args:
        df: Feature DataFrame (output of compute_features with extended=True).
        lower: Lower quantile threshold. Required when compute_thresholds=False.
        upper: Upper quantile threshold. Required when compute_thresholds=False.
        compute_thresholds: When True, derive lower/upper from this DataFrame's
            forward return distribution (use on training split only).

    Returns:
        When compute_thresholds=True:  (X, y, lower_threshold, upper_threshold)
        When compute_thresholds=False: (X, y)

    Raises:
        ValueError: if compute_thresholds=False and lower/upper are not provided.
    """
    if not compute_thresholds and (lower is None or upper is None):
        raise ValueError(
            "Provide lower and upper thresholds, or set compute_thresholds=True."
        )

    df = df.copy()

    # Compute 1-bar-ahead forward return — internal only, not in output
    df["_forward_return"] = (df["close"].shift(-1) - df["close"]) / df["close"]

    # Drop last row (forward return is NaN there)
    df = df.dropna(subset=["_forward_return"]).copy()

    if compute_thresholds:
        lower = float(df["_forward_return"].quantile(0.30))
        upper = float(df["_forward_return"].quantile(0.70))

    # Label: 1 above upper, 0 below lower, drop middle
    mask_long = df["_forward_return"] > upper
    mask_flat = df["_forward_return"] < lower
    labeled = df[mask_long | mask_flat].copy()

    labeled["_label"] = 0
    labeled.loc[mask_long[labeled.index], "_label"] = 1

    # Select only feature columns present in the DataFrame
    feature_cols = [c for c in _FEATURE_COLS if c in labeled.columns]
    X = labeled[feature_cols].copy()
    y = labeled["_label"].copy()

    assert X.index.equals(y.index), "X and y index mismatch"
    assert y.isna().sum() == 0, "Unexpected NaN values in label vector"

    if compute_thresholds:
        return X, y, lower, upper
    return X, y


# ── Phase 3: Volatility-Adjusted Labeling ────────────────────────────────────


def compute_atr(df: pd.DataFrame, window: int = ATR_WINDOW) -> pd.Series:
    """Compute close-to-close Average True Range (ATR).

    ATR measures the *average size* of price moves over the last ``window``
    bars.  It answers: "how much does this asset typically move per bar?"

    A high ATR means the market is volatile (big swings); low ATR means calm.
    We use ATR to normalise forward returns so that a 1% move in a quiet
    market and a 1% move in a turbulent market are treated differently.

    The computation is purely backward-looking — no future leakage.

    Args:
        df:     DataFrame with a 'close' column, sorted ascending by time.
        window: Number of bars to average (default: ATR_WINDOW from config).

    Returns:
        pd.Series of ATR values aligned to df.index.
        The first ``window`` rows are NaN (warm-up period).
    """
    # |close_t - close_{t-1}|: how many dollars did price move this bar?
    abs_close_change = df["close"].diff().abs()
    # Rolling mean of those moves = "typical" move size over the window
    return abs_close_change.rolling(window=window).mean()


def make_vol_adjusted_labels(
    df: pd.DataFrame,
    lower: Optional[float] = None,
    upper: Optional[float] = None,
    compute_thresholds: bool = False,
) -> Union[
    tuple[pd.DataFrame, pd.Series, float, float],
    tuple[pd.DataFrame, pd.Series],
]:
    """Label each bar using ATR-normalised forward returns.

    Unlike ``make_labels`` which uses *raw* forward returns, this function
    first divides the forward return by ATR before applying quantile thresholds.

    **Why normalise?**
    Imagine two scenarios:
      - In a calm week, price rises 0.5% → that's a big move relative to ATR.
      - In a volatile week, price rises 0.5% → that might be noise.

    Raw forward returns treat both identically.  The normalised signal puts
    each move in context: "was this move large or small for this market right now?"

    Normalised signal = (close_{t+1} - close_t) / close_t  /  ATR_t

    Bars with large positive normalised signal → label 1 (long).
    Bars with large negative normalised signal → label 0 (flat).
    The middle 40% is excluded (too noisy to label reliably).

    Args:
        df:                  Feature DataFrame (output of compute_features).
        lower:               Lower quantile threshold. Required when
                             compute_thresholds=False.
        upper:               Upper quantile threshold. Required when
                             compute_thresholds=False.
        compute_thresholds:  When True, derive lower/upper from THIS DataFrame's
                             normalised signal distribution.
                             **Call with True on the training split only.**
                             Using test data to set thresholds would be leakage.

    Returns:
        When compute_thresholds=True:  (X, y, lower_threshold, upper_threshold)
        When compute_thresholds=False: (X, y)

    Raises:
        ValueError: if compute_thresholds=False and lower/upper are not provided.
    """
    if not compute_thresholds and (lower is None or upper is None):
        raise ValueError(
            "Provide lower and upper thresholds, or set compute_thresholds=True."
        )

    df = df.copy()

    # ── Step 1: ATR at each bar ──────────────────────────────────────────────
    # ATR_t = rolling mean of |close_t - close_{t-1}| over ATR_WINDOW bars.
    # This is our measure of "how much does the market typically move per bar?"
    atr = compute_atr(df)

    # ── Step 2: Raw 1-bar-ahead forward return ───────────────────────────────
    # forward_return_t = (close_{t+1} - close_t) / close_t
    # This is the return we would earn by buying at close_t and selling at close_{t+1}.
    forward_return = (df["close"].shift(-1) - df["close"]) / df["close"]

    # ── Step 3: Normalise forward return by ATR ──────────────────────────────
    # normalised_signal_t = forward_return_t / ATR_t
    #
    # Interpretation:
    #   +2.0 → next bar moved UP by twice the typical bar move  → strong buy signal
    #   -2.0 → next bar moved DOWN by twice the typical bar move → strong sell signal
    #    0.1 → tiny move relative to typical → noisy, unreliable signal
    df["_normalized_signal"] = forward_return / atr

    # Drop rows where normalised signal is NaN:
    #   - last row (no next-bar close available)
    #   - first ATR_WINDOW rows (not enough history to compute ATR)
    df = df.dropna(subset=["_normalized_signal"]).copy()

    # ── Step 4: Derive quantile thresholds (on TRAINING data only) ───────────
    if compute_thresholds:
        # P30 = 30th percentile of normalised signals → our lower boundary
        # P70 = 70th percentile                       → our upper boundary
        # Bars between P30 and P70 (the middle 40%) are excluded as too ambiguous.
        lower = float(df["_normalized_signal"].quantile(0.30))
        upper = float(df["_normalized_signal"].quantile(0.70))

    # ── Step 5: Apply binary labels ──────────────────────────────────────────
    mask_long = df["_normalized_signal"] > upper   # large relative up-move  → 1
    mask_flat = df["_normalized_signal"] < lower   # large relative down-move → 0
    labeled = df[mask_long | mask_flat].copy()

    # ── Step 6: Warn if too few bars were labeled ────────────────────────────
    # If less than 20% of bars end up labeled, the thresholds may be too tight,
    # meaning we throw away most of the data and the model sees very few examples.
    labeled_frac = len(labeled) / len(df) if len(df) > 0 else 0.0
    if labeled_frac < 0.20:
        warnings.warn(
            f"Only {labeled_frac:.1%} of bars were labeled after filtering "
            f"(threshold: 20%). Consider looser quantile cutoffs "
            f"(e.g., 0.25/0.75 instead of 0.30/0.70).",
            UserWarning,
        )

    labeled["_label"] = 0
    labeled.loc[mask_long[labeled.index], "_label"] = 1

    feature_cols = [c for c in _FEATURE_COLS if c in labeled.columns]
    X = labeled[feature_cols].copy()
    y = labeled["_label"].copy()

    assert X.index.equals(y.index), "X and y index mismatch"
    assert y.isna().sum() == 0, "Unexpected NaN values in label vector"

    if compute_thresholds:
        return X, y, lower, upper
    return X, y


# ── Phase 4: Daily Volatility-Adjusted Labeling ───────────────────────────────


def make_daily_vol_adjusted_labels(
    df: pd.DataFrame,
    lower: Optional[float] = None,
    upper: Optional[float] = None,
    compute_thresholds: bool = False,
) -> Union[
    tuple[pd.DataFrame, pd.Series, float, float],
    tuple[pd.DataFrame, pd.Series],
]:
    """Label each daily bar using a 5-day ATR-normalised forward return.

    Mirrors ``make_vol_adjusted_labels`` but uses a 5-day forward return
    horizon and 14-day ATR, calibrated for daily bar resolution.

    Normalised signal = (close_{t+5} - close_t) / close_t  /  ATR_14d_t

    Bars with large positive normalised signal → label 1 (long).
    Bars with large negative normalised signal → label 0 (flat).
    The middle 40% is excluded.

    Args:
        df:                  Feature DataFrame (output of compute_features with
                             daily bars; must contain 'close').
        lower:               Lower quantile threshold. Required when
                             compute_thresholds=False.
        upper:               Upper quantile threshold. Required when
                             compute_thresholds=False.
        compute_thresholds:  When True, derive lower/upper from this DataFrame's
                             normalised signal distribution.
                             **Call with True on the training split only.**

    Returns:
        When compute_thresholds=True:  (X, y, lower_threshold, upper_threshold)
        When compute_thresholds=False: (X, y)

    Raises:
        ValueError: if compute_thresholds=False and lower/upper are not provided.
    """
    from bot.config import DAILY_ATR_WINDOW, DAILY_FORWARD_BARS  # noqa: PLC0415

    if not compute_thresholds and (lower is None or upper is None):
        raise ValueError(
            "Provide lower and upper thresholds, or set compute_thresholds=True."
        )

    df = df.copy()

    # ── Step 1: 14-day ATR ───────────────────────────────────────────────────
    atr = compute_atr(df, window=DAILY_ATR_WINDOW)

    # ── Step 2: 5-day forward return ─────────────────────────────────────────
    # forward_return_t = (close_{t+5} - close_t) / close_t
    # shift(-5) aligns close_{t+5} to row t
    forward_return = (df["close"].shift(-DAILY_FORWARD_BARS) - df["close"]) / df["close"]

    # ── Step 3: Normalise by ATR ──────────────────────────────────────────────
    df["_normalized_signal"] = forward_return / atr

    # Drop rows with NaN:
    #   - last DAILY_FORWARD_BARS rows (no forward close available)
    #   - first DAILY_ATR_WINDOW rows (ATR warm-up)
    df = df.dropna(subset=["_normalized_signal"]).copy()

    # ── Step 4: Thresholds (training data only) ───────────────────────────────
    if compute_thresholds:
        lower = float(df["_normalized_signal"].quantile(0.30))
        upper = float(df["_normalized_signal"].quantile(0.70))

    # ── Step 5: Apply binary labels ───────────────────────────────────────────
    mask_long = df["_normalized_signal"] > upper
    mask_flat = df["_normalized_signal"] < lower
    labeled = df[mask_long | mask_flat].copy()

    labeled_frac = len(labeled) / len(df) if len(df) > 0 else 0.0
    if labeled_frac < 0.20:
        warnings.warn(
            f"Only {labeled_frac:.1%} of bars were labeled after filtering "
            f"(threshold: 20%). Consider looser quantile cutoffs.",
            UserWarning,
        )

    labeled["_label"] = 0
    labeled.loc[mask_long[labeled.index], "_label"] = 1

    feature_cols = [c for c in _FEATURE_COLS if c in labeled.columns]
    X = labeled[feature_cols].copy()
    y = labeled["_label"].copy()

    assert X.index.equals(y.index), "X and y index mismatch"
    assert y.isna().sum() == 0, "Unexpected NaN values in label vector"

    if compute_thresholds:
        return X, y, lower, upper
    return X, y
