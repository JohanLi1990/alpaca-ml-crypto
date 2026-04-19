import math

import numpy as np
import pandas as pd

# Hourly bars on a 24/7 crypto market: 24 * 365 = 8760 bars per year
_ANNUALIZATION_FACTOR = math.sqrt(8760)


def compute_metrics(
    results_df: pd.DataFrame,
    prob_series: pd.Series | None = None,
    y_true: pd.Series | None = None,
) -> tuple[dict, dict]:
    """Compute performance metrics for strategy and buy-and-hold.

    Args:
        results_df:  Output of run_backtest(), containing columns:
                     strategy_return, strategy_equity, bnh_return, bnh_equity, signal.
        prob_series: Optional.  Model's predicted P(long) for each bar.
                     When provided alongside ``y_true``, Brier score is added
                     to the strategy metrics dict.
        y_true:      Optional.  Ground-truth binary labels aligned to prob_series.
                     Both prob_series and y_true must be supplied together.

    Returns:
        (strategy_metrics, bnh_metrics) — each is a dict with keys:
            total_return, sharpe_ratio, max_drawdown, num_trades, win_rate
        When prob_series and y_true are provided, strategy_metrics also contains
            brier_score
    """
    strategy_metrics = _metrics_from_series(
        returns=results_df["strategy_return"],
        equity=results_df["strategy_equity"],
        signal=results_df["signal"],
    )
    bnh_metrics = _metrics_from_series(
        returns=results_df["bnh_return"],
        equity=results_df["bnh_equity"],
        signal=None,
    )
    # Optionally augment strategy metrics with Brier score calibration diagnostic
    if prob_series is not None and y_true is not None:
        cal = compute_calibration_metrics(y_true, prob_series)
        strategy_metrics["brier_score"] = cal["brier_score"]

    return strategy_metrics, bnh_metrics


def _metrics_from_series(
    returns: pd.Series,
    equity: pd.Series,
    signal: pd.Series | None,
) -> dict:
    total_return = float(equity.iloc[-1] - 1.0)

    std = returns.std()
    if std == 0 or pd.isna(std):
        sharpe_ratio = 0.0
    else:
        sharpe_ratio = float(returns.mean() / std * _ANNUALIZATION_FACTOR)

    drawdown = (equity / equity.cummax()) - 1
    max_drawdown = float(drawdown.min())

    num_trades, win_rate = _trade_stats(returns, signal)

    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "num_trades": num_trades,
        "win_rate": win_rate,
    }


def _trade_stats(returns: pd.Series, signal: pd.Series | None) -> tuple[int, float]:
    """Compute number of trades and win rate from signal transitions."""
    if signal is None:
        # Buy-and-hold: one perpetual trade — use overall return as win/loss
        return 1, float(1.0 if returns.sum() > 0 else 0.0)

    # Entry = signal changes from 0 to 1
    prev_signal = signal.shift(1).fillna(0)
    entries = (signal == 1) & (prev_signal == 0)
    exits = (signal == 0) & (prev_signal == 1)

    entry_idx = returns.index[entries]
    exit_idx = returns.index[exits]

    num_trades = len(entry_idx)
    if num_trades == 0:
        return 0, 0.0

    wins = 0
    for i, entry in enumerate(entry_idx):
        # Find corresponding exit (next exit after entry)
        future_exits = exit_idx[exit_idx > entry]
        if len(future_exits) == 0:
            # Still in position at end of test window — use last bar as exit
            trade_returns = returns.loc[entry:]
        else:
            exit = future_exits[0]
            trade_returns = returns.loc[entry:exit]
        if trade_returns.sum() > 0:
            wins += 1

    win_rate = wins / num_trades
    return num_trades, float(win_rate)


# ── Phase 3: Calibration & Walk-Forward Summary ───────────────────────────────


def compute_calibration_metrics(
    y_true: pd.Series,
    prob_series: pd.Series,
) -> dict:
    """Measure how well the model's probability forecasts are calibrated.

    A perfectly calibrated model is one where, among all bars where it says
    P(long) = 0.7, roughly 70% should actually be long labels.  Poor
    calibration means the probabilities are misleading.

    Two diagnostics are returned:

    **Brier score** = mean((predicted_prob - actual_label)²)
      Think of it as mean-squared error for probability forecasts.
      - Perfect: 0.0  (model always predicts the right label with full confidence)
      - Random (always predict 0.5): ≈ 0.25
      - Worst:  1.0  (model is always confidently wrong)
      Lower is better.  Values below 0.25 suggest the model has *some* signal.

    **Calibration bins**: divide the probability range [0, 1] into 10 equal
    buckets.  For each bucket, record what fraction of bars in that range
    were actually long.  Plotting predicted vs. actual fraction gives a
    "reliability diagram"; a diagonal line = perfect calibration.

    Args:
        y_true:      Binary label series (0 or 1).  Same index as prob_series.
        prob_series: Predicted P(label=1).  Values in [0.0, 1.0].

    Returns:
        Dict with keys:
            brier_score      — float in [0.0, 1.0]
            calibration_bins — dict mapping bin centre → {"mean_predicted_prob",
                               "fraction_positive"}

    Raises:
        ValueError: if y_true and prob_series have different indices.
    """
    from sklearn.calibration import calibration_curve  # noqa: PLC0415

    if not y_true.index.equals(prob_series.index):
        raise ValueError(
            "y_true and prob_series must share the same index.  "
            f"Got {len(y_true)} vs {len(prob_series)} rows."
        )

    # Drop rows where either series is NaN before any computation
    mask = y_true.notna() & prob_series.notna()
    y_np = y_true[mask].to_numpy(dtype=float)
    p_np = prob_series[mask].to_numpy(dtype=float)

    # ── Brier Score ──────────────────────────────────────────────────────────
    # For each bar: (predicted_prob − actual_label)²
    # Then average across all bars.
    # Example: model predicts 0.8 but label = 0 → error = (0.8 − 0)² = 0.64
    #          model predicts 0.8 and label = 1 → error = (0.8 − 1)² = 0.04
    brier_score = float(np.mean((p_np - y_np) ** 2))

    # ── Calibration Bins ─────────────────────────────────────────────────────
    # Divide probabilities into 10 equal-width buckets: [0,0.1), [0.1,0.2), …
    # For each non-empty bucket, ask: "of the bars where the model predicted
    # in this range, what fraction were actually long?"
    # sklearn's calibration_curve automatically skips empty buckets.
    try:
        fraction_pos, mean_pred = calibration_curve(
            y_np, p_np, n_bins=10, strategy="uniform"
        )
        calibration_bins = {
            round(float(mp), 4): {
                "mean_predicted_prob": float(mp),
                "fraction_positive": float(fp),
            }
            for mp, fp in zip(mean_pred, fraction_pos)
        }
    except ValueError:
        # Can happen with very few samples or a single class — return empty
        calibration_bins = {}

    return {
        "brier_score": brier_score,
        "calibration_bins": calibration_bins,
    }


def compute_walkforward_summary(folds: list[dict]) -> dict:
    """Aggregate per-fold walk-forward results into summary statistics.

    Folds where an exception occurred have all metric values set to None and
    are excluded from every aggregation.

    Think of this like a report card across multiple exam periods: instead of
    one exam (Phase 2 single test split), we have N exams and we compute the
    median grade.  A consistently positive Sharpe across folds is much stronger
    evidence of a real edge than a single good test.

    Args:
        folds: List of fold result dicts from ``run_walkforward()``.

    Returns:
        Dict with aggregate statistics:
            median_sharpe        — middle value of per-fold Sharpe ratios
            std_sharpe           — spread (standard deviation) of Sharpe ratios
            best_sharpe          — best single-fold Sharpe
            worst_sharpe         — worst single-fold Sharpe
            median_total_return  — median profit/loss across folds
            median_max_drawdown  — median worst peak-to-trough loss
            median_num_trades    — median trade count
            median_win_rate      — median fraction of winning trades
            n_folds              — number of valid (non-skipped) folds
    """
    import statistics  # noqa: PLC0415

    # Keep only folds where the metrics were successfully computed
    valid = [f for f in folds if f.get("sharpe_ratio") is not None]
    n_valid = len(valid)

    # Edge case: all folds failed
    if n_valid == 0:
        return {
            "median_sharpe": None,
            "std_sharpe": None,
            "best_sharpe": None,
            "worst_sharpe": None,
            "median_total_return": None,
            "median_max_drawdown": None,
            "median_num_trades": None,
            "median_win_rate": None,
            "n_folds": 0,
        }

    sharpes = [f["sharpe_ratio"] for f in valid]
    returns = [f["total_return"] for f in valid]
    drawdowns = [f["max_drawdown"] for f in valid]
    trades = [f["num_trades"] for f in valid]
    win_rates = [f["win_rate"] for f in valid]

    return {
        # Sharpe ratio: return per unit of risk.
        # > 0 means better than random; > 1 is considered good; > 2 is excellent.
        "median_sharpe": statistics.median(sharpes),
        "std_sharpe": statistics.stdev(sharpes) if n_valid > 1 else 0.0,
        "best_sharpe": max(sharpes),
        "worst_sharpe": min(sharpes),
        # Total return: e.g., 0.05 = +5% profit over the test period
        "median_total_return": statistics.median(returns),
        # Max drawdown: e.g., -0.10 = fell 10% from peak before recovering
        "median_max_drawdown": statistics.median(drawdowns),
        "median_num_trades": statistics.median(trades),
        "median_win_rate": statistics.median(win_rates),
        "n_folds": n_valid,
    }
