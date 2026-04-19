import pandas as pd

from bot.config import ABSTAIN_HI, ABSTAIN_LO, MIN_HOLD_BARS, TRANSACTION_FEE


def apply_signal_policy(
    prob_series: pd.Series,
    abstain_lo: float = ABSTAIN_LO,
    abstain_hi: float = ABSTAIN_HI,
    min_hold_bars: int = MIN_HOLD_BARS,
) -> pd.Series:
    """Convert model probability forecasts into a discrete trading signal.

    The model outputs P(long) ∈ [0, 1] for every bar.  Naively trading
    whenever P > 0.5 generates excessive turnover; transaction fees
    eliminate any edge.  This policy enforces two disciplines:

    1. **Abstain band**: only trade when the model is genuinely confident.
       - P > abstain_hi  → signal = 1  (confident long: enter/stay long)
       - P < abstain_lo  → signal = 0  (bearish: exit / stay flat)
       - abstain_lo ≤ P ≤ abstain_hi → signal = 0  (uncertain: do nothing)

    2. **Minimum hold** (min_hold_bars > 1): once we enter a long position,
       hold it for at least min_hold_bars bars to avoid rapid-fire entry/exit.
       The hold is released early only if probability drops *below* abstain_lo
       (genuine bearish signal), but NOT just because it falls into the
       abstain band (mere uncertainty does not override the hold).

    Args:
        prob_series:    pd.Series of P(label=1) values in [0.0, 1.0].
        abstain_lo:     Probability below which we are bearish (default 0.45).
        abstain_hi:     Probability above which we are bullish (default 0.55).
        min_hold_bars:  Minimum bars to hold after entry (default 1 = no hold).

    Returns:
        Integer pd.Series (0=flat, 1=long) with the same index as prob_series.
        Contains no NaN values.
    """
    signals: list[int] = []

    # how many more bars we are committed to holding after this one
    hold_remaining: int = 0

    for prob in prob_series:
        if prob > abstain_hi:
            # ── Confident long signal ────────────────────────────────────────
            # Enter (or extend) the long position.
            # After this bar we commit to (min_hold_bars - 1) more held bars
            # because this bar already counts as bar 1 of the hold.
            signals.append(1)
            hold_remaining = min_hold_bars - 1

        elif hold_remaining > 0:
            # ── Inside a hold period ─────────────────────────────────────────
            if prob < abstain_lo:
                # Strong bearish signal → release the hold early
                signals.append(0)
                hold_remaining = 0
            else:
                # Uncertainty (abstain band) → honour the hold, stay long
                signals.append(1)
                hold_remaining -= 1

        else:
            # ── Not in a hold, not confident ─────────────────────────────────
            signals.append(0)

    return pd.Series(signals, index=prob_series.index, dtype=int)


def run_backtest(
    df: pd.DataFrame,
    fee: float = TRANSACTION_FEE,
    policy_fn=None,
) -> pd.DataFrame:
    """Simulate strategy performance on historical bars with signals.

    When ``policy_fn`` is provided it is applied to the ``signal`` column
    *before* the one-bar lag, allowing the walk-forward harness to inject
    the abstain-band policy without modifying the input DataFrame.
    When omitted the function behaves identically to Phase 2.

    The signal at bar t is applied to bar t+1 (one-bar lag to avoid
    look-ahead). Transaction costs are deducted when the position changes.

    Args:
        df: DataFrame with ``close`` and ``signal`` columns (signal is int
            0=flat, 1=long). Rows must be sorted ascending by time.
        fee: Flat fee deducted per position change (default: TRANSACTION_FEE).

    Returns:
        DataFrame with the original columns plus:
            bar_return      — (close_t - close_{t-1}) / close_{t-1}
            position        — lagged signal (position held during bar t)
            trade           — 1 where position changes, else 0
            strategy_return — bar return × position − fee × trade
            strategy_equity — cumulative equity starting at 1.0
            bnh_return      — bar return (continuous long, no fees)
            bnh_equity      — cumulative buy-and-hold equity starting at 1.0
    """
    result = df.copy()

    # Optional: transform the raw signal through a policy function
    # (e.g., the abstain-band policy that filters uncertain predictions).
    # This must happen BEFORE the lag so the policy sees the original signal.
    if policy_fn is not None:
        result["signal"] = policy_fn(result["signal"])

    # Bar return at time t
    result["bar_return"] = result["close"].pct_change()

    # Position: signal from prior bar (lag=1 to avoid look-ahead)
    result["position"] = result["signal"].shift(1).fillna(0)

    # Trade flag: 1 wherever position changes
    result["trade"] = (result["position"] != result["position"].shift(1)).astype(int)
    # First bar has no prior — treat as no trade
    result.iloc[0, result.columns.get_loc("trade")] = 0

    # Strategy return: position × bar return − fee on position changes
    result["strategy_return"] = (
        result["position"] * result["bar_return"] - fee * result["trade"]
    )

    # Buy-and-hold return: always long, no fees
    result["bnh_return"] = result["bar_return"]

    # Equity curves — fill NaN on first bar with 0 for compounding
    result["strategy_return"] = result["strategy_return"].fillna(0)
    result["bnh_return"] = result["bnh_return"].fillna(0)

    result["strategy_equity"] = (1 + result["strategy_return"]).cumprod()
    result["bnh_equity"] = (1 + result["bnh_return"]).cumprod()

    return result
