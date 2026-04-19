"""Regime and cross-asset feature computation for Phase 3.

Regime features describe the *market state* rather than individual bar moves.
They help the model answer questions like:
  - Is the market currently calm or turbulent?  (vol_percentile)
  - Is price drifting up or down over the past day?  (trend_slope)
  - Was today's return large or small for this market?  (atr_normalized_return)

Cross-asset features add relative context:
  - Is BTC outperforming or underperforming ETH/SOL lately?

All features are computed using only data available at or before bar t
(no future leakage).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from bot.config import ATR_WINDOW, DAILY_REGIME_VOL_WINDOW, DAILY_TREND_SLOPE_WINDOW, REGIME_VOL_WINDOW, TREND_SLOPE_WINDOW
from bot.features.labeling import compute_atr

# Number of bars used for the rolling return spread (cross-asset features)
_SPREAD_WINDOW = 12


def compute_regime_features(df: pd.DataFrame, timeframe: str = "hourly") -> pd.DataFrame:
    """Add market regime features to a feature DataFrame.

    New columns added:
        vol_percentile       — 0 (low vol), 1 (medium), 2 (high vol), based on
                               how current 20-bar volatility ranks vs. the last
                               N bars (252 for hourly, 60 for daily)
        trend_slope          — OLS slope of close over the last N bars
                               (24 for hourly, 10 for daily), normalised by
                               rolling_std (dimensionless)
        atr_normalized_return — bar return / ATR: how big was this bar's move
                               relative to the market's typical move size?

    Warm-up rows where any feature is NaN are dropped before returning.

    Args:
        df:        Feature DataFrame produced by compute_features (must contain
                   columns: close, return, rolling_std).
        timeframe: ``"hourly"`` (default) or ``"daily"`` — selects window sizes.

    Returns:
        Input DataFrame with three regime columns appended; NaN rows removed.
    """
    df = df.copy()

    # Select window sizes based on timeframe
    vol_window = DAILY_REGIME_VOL_WINDOW if timeframe == "daily" else REGIME_VOL_WINDOW
    slope_window = DAILY_TREND_SLOPE_WINDOW if timeframe == "daily" else TREND_SLOPE_WINDOW

    # ── 1. Volatility Percentile ─────────────────────────────────────────────
    # rolling_std (already in df from compute_features) measures the spread of
    # close prices over the last 20 bars — a proxy for short-term volatility.
    #
    # We ask: "compared to the past vol_window bars, is today's
    # volatility low, medium, or high?"
    #
    # rolling().rank(pct=True) computes the fraction of past values that are
    # below the current value.  e.g., 0.9 means 90% of past volatilities
    # were lower → we're in a high-vol regime.
    vol_rank = df["rolling_std"].rolling(window=vol_window).rank(pct=True)

    # Bucket the [0, 1] percentile rank into three integer regime labels:
    #   0 = low volatility  (bottom third, < 0.333)
    #   1 = medium          (middle third, 0.333–0.667)
    #   2 = high volatility (top third, > 0.667)
    df["vol_percentile"] = pd.cut(
        vol_rank,
        bins=[-0.001, 1 / 3, 2 / 3, 1.001],
        labels=[0, 1, 2],
    ).astype("Int64")  # Int64 supports NaN (unlike plain int64)

    # ── 2. Trend Slope ───────────────────────────────────────────────────────
    # Fit a straight line (y = a·x + b) through the last slope_window
    # close prices.  The slope 'a' tells us: "is price trending up or down,
    # and how fast?"
    #
    # We normalise the raw slope (in $/bar) by rolling_std (also in $) so the
    # result is dimensionless and comparable across different price levels.
    # Positive trend_slope → uptrend; negative → downtrend; near 0 → choppy.
    def _ols_slope(prices: np.ndarray) -> float:
        """Return the OLS linear slope over equally-spaced bars."""
        # np.polyfit returns [slope, intercept]; we only need the slope
        x = np.arange(len(prices))
        return float(np.polyfit(x, prices, 1)[0])

    raw_slope = (
        df["close"]
        .rolling(window=slope_window)
        .apply(_ols_slope, raw=True)
    )
    # Divide by rolling_std → slope in "standard-deviation units per bar"
    df["trend_slope"] = raw_slope / df["rolling_std"]

    # ── 3. ATR-Normalized Return ─────────────────────────────────────────────
    # return_t = (close_t - close_{t-1}) / close_{t-1}  (already in df)
    # ATR_t    = average |close change| over the last ATR_WINDOW bars
    #
    # Dividing return by ATR puts the return in context:
    #   atr_normalized_return = 1.0  means "this bar moved exactly as much as usual"
    #   atr_normalized_return = 2.0  means "this bar moved twice the average move"
    atr = compute_atr(df, window=ATR_WINDOW)
    df["atr_normalized_return"] = df["return"] / atr

    # ── Drop warm-up rows where any regime feature is NaN ───────────────────
    # (vol_percentile needs REGIME_VOL_WINDOW bars; trend_slope needs
    #  TREND_SLOPE_WINDOW; atr_normalized_return needs ATR_WINDOW)
    df = df.dropna(
        subset=["vol_percentile", "trend_slope", "atr_normalized_return"]
    ).copy()

    # vol_percentile was stored as nullable Int64 — convert to plain int now
    # that NaN rows are gone
    df["vol_percentile"] = df["vol_percentile"].astype(int)

    return df


def compute_cross_asset_features(
    dfs: dict[str, pd.DataFrame],
    ref_symbol: str = "BTC/USD",
) -> pd.DataFrame:
    """Add cross-asset return-spread features to the reference symbol's DataFrame.

    For each companion symbol, computes:
        {ref}_excess_return_vs_{companion} = rolling _SPREAD_WINDOW-bar sum of
            (ref_return_t - companion_return_t)

    A positive value means the reference has been *outperforming* the companion
    over the last _SPREAD_WINDOW hours; negative means underperforming.
    This captures relative momentum, which can be a leading indicator of
    mean-reversion or trend continuation.

    Only rows present in ALL symbol DataFrames are kept (index intersection),
    so a missing candle in one symbol doesn't corrupt the others.

    Args:
        dfs: Dict mapping symbol string → feature DataFrame, e.g.
             {"BTC/USD": df_btc, "ETH/USD": df_eth, "SOL/USD": df_sol}.
             Each DataFrame must have a 'return' column.
        ref_symbol: The reference symbol to enrich (default: "BTC/USD").

    Returns:
        The reference symbol's DataFrame with cross-asset columns appended.
        Warm-up rows (first _SPREAD_WINDOW - 1 bars) are dropped.

    Raises:
        KeyError: if ref_symbol is not found in dfs.
    """
    if ref_symbol not in dfs:
        raise KeyError(f"Reference symbol '{ref_symbol}' not found in dfs.")

    df_ref = dfs[ref_symbol].copy()

    # Align all DataFrames to the intersection of their timestamp indices.
    # If BTC has a bar at 14:00 but ETH doesn't, we drop that bar from all.
    common_index = df_ref.index
    for df_sym in dfs.values():
        common_index = common_index.intersection(df_sym.index)

    df_ref = df_ref.loc[common_index].copy()

    # Normalise symbol names for column names: "BTC/USD" → "btc"
    ref_slug = ref_symbol.split("/")[0].lower()

    for sym, df_sym in dfs.items():
        if sym == ref_symbol:
            continue  # skip — we don't compute a spread vs. ourselves

        # Graceful handling: warn instead of crash if companion is missing
        if sym not in dfs:
            warnings.warn(
                f"Companion symbol '{sym}' missing from dfs; "
                f"skipping excess return column.",
                UserWarning,
            )
            continue

        companion_slug = sym.split("/")[0].lower()
        col_name = f"{ref_slug}_excess_return_vs_{companion_slug}"

        df_companion = dfs[sym].loc[common_index]

        # Per-bar spread: how much more (or less) did reference move vs companion?
        spread = df_ref["return"] - df_companion["return"]

        # Rolling sum over _SPREAD_WINDOW bars:
        # "Over the last 12 hours, how much has BTC outperformed ETH in total?"
        df_ref[col_name] = spread.rolling(window=_SPREAD_WINDOW).sum()

    # Drop warm-up rows where the rolling sum hasn't filled yet
    cross_cols = [c for c in df_ref.columns if "_excess_return_vs_" in c]
    if cross_cols:
        df_ref = df_ref.dropna(subset=cross_cols).copy()

    return df_ref
