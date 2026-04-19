## 1. Dependencies and Environment

- [x] 1.1 Add `xgboost` and `shap` to `requirements.txt`
- [x] 1.2 Verify `xgboost` and `shap` are importable in the `strategy-lab` conda environment; install if missing

## 2. Daily Bar Fetching

- [x] 2.1 Extend `fetch_bars_range` in `bot/data/fetcher.py` to accept `TimeFrame.Day` as a valid `timeframe` argument
- [x] 2.2 Add `fetch_daily_bars(symbol, days_back=730)` convenience function to `bot/data/fetcher.py` that anchors the date range to today minus `days_back` calendar days
- [ ] 2.3 Verify that `fetch_daily_bars("BTC/USD")` returns ≥600 rows after preprocessing
- [ ] 2.4 Verify that the exclude-last-bar convention is applied when daily bars are fetched

## 3. Daily Target Labeling

- [x] 3.1 Add `make_daily_vol_adjusted_labels(df, compute_thresholds=False, lower=None, upper=None)` to `bot/features/labeling.py`
- [x] 3.2 Implement 14-day ATR denominator using rolling mean of `|close[t] - close[t-1]|`
- [x] 3.3 Implement 5-day forward return numerator (`close[t+5] - close[t]`)
- [x] 3.4 Implement quantile-threshold computation from training data (`compute_thresholds=True` path), returning `(X, y, lower, upper)`
- [x] 3.5 Implement threshold-application path for test data, returning `(X, y)` without recalculation
- [x] 3.6 Confirm that the last 5 rows of any input are dropped (no valid forward return) and NaNs are removed

## 4. Daily Feature Engineering

- [x] 4.1 Add `timeframe` parameter to `compute_features` in `bot/features/rolling.py` (default: `"hourly"`)
- [x] 4.2 Implement daily-scaled base features: lagged returns (1, 2, 3 days), 5-day and 20-day momentum, 5-day volume z-score
- [x] 4.3 Implement daily-scaled regime features in `bot/features/regime.py`: `vol_percentile` (60-bar window), `trend_slope` (10-bar OLS), `atr_normalized_return` (14-bar ATR)
- [x] 4.4 Wire the `timeframe="daily"` parameter so `compute_features(df, extended=True, regime=True, timeframe="daily")` uses the daily-scaled windows
- [x] 4.5 Verify no NaN values in any column for a well-formed daily DataFrame after warm-up rows are dropped

## 5. XGBoost Model

- [x] 5.1 Create `bot/models/xgboost_model.py` with `train_xgboost(X_train, y_train)` function
- [x] 5.2 Configure `XGBClassifier` with `eval_metric="logloss"`, `use_label_encoder=False`, `n_estimators=200`
- [x] 5.3 Implement `GridSearchCV` with `TimeSeriesSplit(n_splits=3)` over: `max_depth` ∈ [2, 3, 4], `learning_rate` ∈ [0.05, 0.1, 0.2], `subsample` ∈ [0.7, 0.9]
- [x] 5.4 Return best estimator (by mean cross-validation log-loss) from `train_xgboost`
- [x] 5.5 Add `save_xgboost(model, path)` that saves model to `.json` using XGBoost native serialisation
- [x] 5.6 Add `load_xgboost(path)` that restores the model from the `.json` artifact and returns a ready-to-predict `XGBClassifier`

## 6. SHAP Feature Importance

- [x] 6.1 Add `compute_shap_importance(model, X_test)` function in `bot/models/xgboost_model.py` that creates a `shap.TreeExplainer` and returns a dict of `feature_name → mean_abs_shap_value` sorted descending
- [x] 6.2 Wire `compute_shap_importance` into `run_walkforward` so each fold result dict includes `shap_importance`
- [x] 6.3 Verify that `shap_importance` dict has one entry per feature column and values are non-negative floats

## 7. Walk-Forward Config for Daily Bars

- [x] 7.1 Add daily walk-forward constants to `bot/config.py`: `DAILY_WALKFORWARD_TRAIN_BARS=400`, `DAILY_WALKFORWARD_VAL_BARS=100`, `DAILY_WALKFORWARD_TEST_BARS=100`, `DAILY_WALKFORWARD_N_FOLDS=4`
- [x] 7.2 Verify that with 730 daily bars and the above config, folds 1–3 execute and fold 4 is skipped (consistent with Phase 3 behaviour)

## 8. Research Notebook

- [x] 8.1 Create `notebooks/phase4_daily_xgboost.ipynb` with section headers mirroring Phase 3 notebook structure
- [x] 8.2 Add Section 1: Setup — imports, config constants, credentials
- [x] 8.3 Add Section 2: Data — call `fetch_daily_bars` for BTC/USD, ETH/USD, SOL/USD; print shape and date range
- [x] 8.4 Add Section 3: Feature check — run `compute_features(df, extended=True, regime=True, timeframe="daily")` on BTC; print column list and head
- [x] 8.5 Add Section 4: Label check — run `make_daily_vol_adjusted_labels` on BTC training slice; print class balance
- [x] 8.6 Add Section 5: Walk-forward loop — for each symbol, call `run_walkforward` using `fetch_daily_bars`, `compute_features`, `make_daily_vol_adjusted_labels`, `train_xgboost`, `apply_signal_policy`; collect fold results
- [x] 8.7 Add Section 6: Per-fold metrics table — display `fold`, `sharpe_ratio`, `total_return`, `max_drawdown`, `brier_score` per symbol
- [x] 8.8 Add Section 7: SHAP importance — display per-fold `shap_importance` rankings for each symbol; note consistent vs inconsistent features
- [x] 8.9 Add Section 8: Kill criterion evaluation — compute median OOS Sharpe per symbol; print PASS/FAIL for ≥2 of 3 symbols > 0

## 9. Integration Checks

- [x] 9.1 Confirm `bot/strategies/logreg.py` and `bot/strategies/zscore.py` are unchanged (no regressions)
- [x] 9.2 Confirm `run_backtest` and `run_walkforward` (Phase 3 harness) work without modification when passed an XGBoost `model_fn`
- [ ] 9.3 Run the full notebook end-to-end and confirm no runtime errors
- [ ] 9.4 Confirm fold 4 is skipped with a `UserWarning` (not a crash) for all three symbols
