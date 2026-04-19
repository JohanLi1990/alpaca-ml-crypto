## Why

Phases 2 and 3 confirmed that logistic regression on 1-hour bars has no reliable predictive edge on BTC/ETH/SOL — Brier scores near 0.25 (random baseline) and consistently negative walk-forward Sharpe ratios. The 1-hour direction signal is near-random noise: too short a horizon for any pattern to be statistically durable. Phase 4 targets the two root causes simultaneously: move to the daily timeframe where structure has a higher signal-to-noise ratio, and replace logistic regression with XGBoost (gradient-boosted trees) which can capture non-linear regime interactions that a linear classifier cannot.

## What Changes

- Replace the 1-hour OHLCV bar fetcher with a daily bar fetcher (Alpaca `Day` timeframe) covering a longer lookback window (~2 years / 730 days)
- Replace `make_vol_adjusted_labels` with a daily equivalent that labels over a 5-day forward return horizon, normalised by 14-day ATR
- Replace logistic regression model training with XGBoost classifier training, including a time-series-safe hyperparameter search (`TimeSeriesSplit` + `GridSearchCV`) over depth, learning rate, and subsample
- Keep the full Phase 3 walk-forward harness, signal policy, and calibration metrics — swapping only the bar resolution and model class
- Add SHAP value logging per fold so feature importance is tracked across folds

## Capabilities

### New Capabilities

- `daily-bar-fetching`: Fetch and cache OHLCV bars at the `Day` timeframe for a configurable symbol and date range; wraps the existing bar-fetching capability with a daily-specific default config and date arithmetic for the ~2-year lookback.
- `xgboost-model`: Train, cross-validate, and persist an XGBoost classifier for directional prediction; load it at inference time; expose SHAP feature-importance logging alongside the model artifact.
- `daily-target-labeling`: Label each daily bar using a 5-day ATR-normalised forward return, using training-data thresholds only. Mirrors `make_vol_adjusted_labels` at daily resolution.

### Modified Capabilities

- `ml-feature-engineering`: Adapt all existing features (lagged returns, momentum, volume z-score, regime features) for daily bars — lookback windows shrink proportionally (e.g., 252-bar vol percentile becomes 60-bar on daily). Existing `compute_features` contract preserved; new `timeframe="daily"` parameter added.
- `bar-fetching`: Add `TimeFrame.Day` as a supported timeframe parameter alongside existing `Hour` support.

## Impact

- **New dependency**: `xgboost`, `shap` (pip-installable; no conda channel issues)
- **New modules**: `bot/strategies/xgboost_strat.py` (daily signal generator), `bot/models/` (XGBoost artifact `.json`)
- **Modified modules**: `bot/data/fetcher.py` (Day timeframe), `bot/features/rolling.py` (daily window params), `bot/features/labeling.py` (5-day label), `bot/config.py` (new daily constants)
- **New entry point**: `notebooks/phase4_daily_xgboost.ipynb`
- **Phase 1–3 unchanged**: all existing strategies, backtest engine, walk-forward harness, and signal policy are fully preserved
