## Why

Phase 2 confirmed that simple price-based features (rolling mean, z-score, lags, momentum) have no reliable predictive edge over buy-and-hold on crypto. The pipeline itself is sound — it revealed a negative result, which is valuable. Phase 3 now diagnoses *why* the edge is absent and introduces structural improvements across three dimensions: better labels (volatility-adjusted targets that align with tradeable moves), better features (regime-aware and normalized signals), and a walk-forward evaluation harness that makes edge detection statistically credible across symbols and time windows.

## What Changes

- Replace 1-bar direction labels with volatility-normalized forward return labels (return-to-ATR ratio) to filter out noise from large move targets that the model cannot predict linearly
- Extend the feature set with regime features (realized vol regime, trend regime, ATR-normalized return) and cross-asset relative strength (BTC/ETH/SOL return spread) to give the model signals that vary by market state
- Add a walk-forward evaluation framework: rolling train/validate/test windows stepped through time, replacing the single static 80/20 split
- Add a cost-aware signal policy: abstain band (no trade when confidence is near 0.5), minimum hold bars, and maximum daily turnover cap to structurally reduce fee drag
- Add calibration-awareness: report Brier score and reliability diagram alongside Sharpe/drawdown to detect when model probabilities are miscalibrated
- Extend the research notebook to run the walk-forward harness and surface median/dispersion metrics across folds

## Capabilities

### New Capabilities

- `volatility-adjusted-labeling`: Label each bar using the ratio of forward return to realized ATR (average true range), so labels capture moves significant relative to the prevailing volatility regime. Computed on training data only (no leakage).
- `regime-features`: Compute per-bar regime signals: realized vol percentile (low/medium/high bucket), trend regime (slope of close over N bars), ATR-normalized return. All leakage-free.
- `cross-asset-features`: Compute relative strength features: rolling return spread between two symbols (e.g., BTC excess return vs ETH), correlation regime indicator.
- `walk-forward-harness`: Implement a rolling walk-forward evaluation loop that produces per-fold metrics (total return, Sharpe, max drawdown, trades, win rate), and aggregate summary statistics (median, std, best, worst fold).
- `cost-aware-signal-policy`: Implement an abstain band and minimum hold rule on top of model probabilities, making signal frequency and fee drag explicit parameters.
- `model-calibration-metrics`: Compute Brier score and optionally plot a reliability diagram (calibration curve) to diagnose probability quality independent of classification accuracy.

### Modified Capabilities

- `ml-feature-engineering`: Extend with regime and cross-asset features (ATR-normalized return, vol percentile, trend slope, return spread). Existing 9 Phase 2 features retained; new features added alongside under `extended=True`.
- `target-labeling`: Add alternative volatility-adjusted labeling path alongside the existing quantile-based path. Existing `make_labels` API preserved; new function `make_vol_adjusted_labels` added.
- `vectorized-backtest`: Extend `run_backtest` to accept a signal policy object (abstain threshold, min hold bars) so cost-aware policies are exercised within the same backtest infrastructure.
- `performance-metrics`: Add Brier score, calibration score, median-across-folds metrics, and a `compute_walkforward_summary` function aggregating per-fold dicts into summary statistics.

## Impact

- **New modules**: `bot/features/regime.py` (regime + cross-asset features), `bot/backtest/walkforward.py` (rolling harness)
- **Modified modules**: `bot/features/rolling.py` (new extended cols), `bot/features/labeling.py` (vol-adjusted labeling), `bot/backtest/engine.py` (signal policy params), `bot/backtest/metrics.py` (Brier score + fold aggregation)
- **New entry point**: `notebooks/phase3_robustness.ipynb`
- **No new live bot strategies**: walk-forward and calibration are research/evaluation tools only; the live bot `--strategy logreg` is unchanged until a strategy passes the Phase 3 acceptance gate
- **No new external dependencies**: ATR computable from OHLCV (already fetched); calibration via `sklearn.calibration` (already in environment)
