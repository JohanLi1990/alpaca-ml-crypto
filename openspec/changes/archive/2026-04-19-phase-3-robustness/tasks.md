## 1. Dependencies & Config

- [x] 1.1 Add `ATR_WINDOW = 14`, `REGIME_VOL_WINDOW = 252`, `TREND_SLOPE_WINDOW = 24`, `WALKFORWARD_TRAIN_BARS = 1800`, `WALKFORWARD_VAL_BARS = 600`, `WALKFORWARD_TEST_BARS = 600`, `WALKFORWARD_N_FOLDS = 4`, `ABSTAIN_LO = 0.45`, `ABSTAIN_HI = 0.55`, `MIN_HOLD_BARS = 1` constants to `bot/config.py`
- [x] 1.2 Create `bot/features/regime.py` with module stub and docstring
- [x] 1.3 Create `bot/backtest/walkforward.py` with module stub and docstring

## 2. Volatility-Adjusted Labeling

- [x] 2.1 Add `compute_atr(df, window=ATR_WINDOW)` helper in `bot/features/labeling.py` that computes 14-bar close-to-close ATR and returns a Series with NaN for warm-up rows
- [x] 2.2 Implement `make_vol_adjusted_labels(df, lower=None, upper=None, compute_thresholds=False)` in `bot/features/labeling.py` using ATR-normalized forward return as the labeling signal
- [x] 2.3 Implement quantile threshold computation (`compute_thresholds=True`) in `make_vol_adjusted_labels` — thresholds derived from normalized signal distribution on training data only
- [x] 2.4 Implement minimum labeled fraction guard: emit `UserWarning` when labeled fraction drops below 20%
- [x] 2.5 Verify `make_vol_adjusted_labels` returns `(X, y, lower, upper)` or `(X, y)` with aligned index and no NaN in `y`
- [x] 2.6 Verify `make_labels` (Phase 2) is unchanged and all Phase 2 labeling tests still pass

## 3. Regime Features

- [x] 3.1 Implement `compute_atr(df, window)` (shared logic with labeling; prefer importing from a shared utility or duplicating to keep module independence) in `bot/features/regime.py`
- [x] 3.2 Implement `vol_percentile` in `compute_regime_features(df)`: rolling 252-bar percentile rank of `rolling_std_20`, bucketed to `{0, 1, 2}`
- [x] 3.3 Implement `trend_slope` in `compute_regime_features(df)`: OLS slope of close over 24 bars, normalized by `rolling_std`
- [x] 3.4 Implement `atr_normalized_return` in `compute_regime_features(df)`: `return_t / ATR_t`
- [x] 3.5 Verify all regime features contain no NaN after warm-up drop and use only data at or before bar `t`
- [x] 3.6 Verify `compute_regime_features` returns input DataFrame with the three new columns appended

## 4. Cross-Asset Features

- [x] 4.1 Implement `compute_cross_asset_features(dfs: dict, ref_symbol: str = "BTC/USD")` in `bot/features/regime.py` that aligns DataFrames by timestamp index intersection
- [x] 4.2 Implement rolling 12-bar return spread `btc_excess_return_vs_eth` and `btc_excess_return_vs_sol` columns using only data at or before bar `t`
- [x] 4.3 Implement graceful handling when a companion symbol is absent: skip the column and emit `UserWarning`
- [x] 4.4 Drop warm-up rows (first 11 bars of cross-asset features) from output
- [x] 4.5 Verify output DataFrame contains the reference symbol's original columns plus cross-asset spread columns with no NaN

## 5. Extended Feature Integration

- [x] 5.1 Add `regime=False` parameter to `compute_features` in `bot/features/rolling.py`
- [x] 5.2 When `regime=True`, call `compute_regime_features(df)` after base + extended feature computation and append its columns to the output DataFrame
- [x] 5.3 Verify `compute_features(df, extended=True, regime=True)` returns 12 feature columns (9 Phase 2 + 3 regime) with no NaN
- [x] 5.4 Verify `compute_features(df, extended=True)` still returns the same 9 Phase 2 columns unchanged (no regression)
- [x] 5.5 Verify `compute_features(df)` (base only, Phase 1 path) is completely unaffected

## 6. Cost-Aware Signal Policy

- [x] 6.1 Implement `apply_signal_policy(prob_series, abstain_lo=ABSTAIN_LO, abstain_hi=ABSTAIN_HI, min_hold_bars=MIN_HOLD_BARS)` in `bot/backtest/engine.py`
- [x] 6.2 Implement abstain band: bars with `abstain_lo <= prob <= abstain_hi` produce signal `0`
- [x] 6.3 Implement minimum hold: once signal becomes `1`, maintain it for `min_hold_bars` bars unless probability falls below `abstain_lo`
- [x] 6.4 Verify output Series has the same index as input, dtype int, and no NaN values
- [x] 6.5 Verify default parameters match `ABSTAIN_LO`, `ABSTAIN_HI`, `MIN_HOLD_BARS` from config

## 7. Optional Policy Hook in Backtest Engine

- [x] 7.1 Add `policy_fn=None` parameter to `run_backtest` in `bot/backtest/engine.py`
- [x] 7.2 When `policy_fn` is not None, apply it to the signal column before lagging: `df["signal"] = policy_fn(df["signal"])`
- [x] 7.3 Verify `run_backtest(df)` without `policy_fn` produces identical results to Phase 2 behavior

## 8. Walk-Forward Harness

- [x] 8.1 Implement `run_walkforward(df, n_folds, train_bars, val_bars, test_bars, feature_fn, label_fn, model_fn, policy_fn)` in `bot/backtest/walkforward.py`
- [x] 8.2 Implement rolling fold slicing: each fold shifts the test window by `test_bars` bars with no overlap between test windows across folds
- [x] 8.3 Ensure label thresholds are recomputed from training data within each fold (no cross-fold leakage)
- [x] 8.4 Run per-fold: feature_fn → label_fn → model_fn → policy_fn → run_backtest → compute_metrics; store results as a per-fold dict
- [x] 8.5 Implement skip-and-continue for folds that raise exceptions: log a warning, record `None` metrics, continue
- [x] 8.6 Verify per-fold result dicts contain all required keys: `fold`, `train_start`, `train_end`, `test_start`, `test_end`, `total_return`, `sharpe_ratio`, `max_drawdown`, `num_trades`, `win_rate`, `brier_score`

## 9. Calibration Metrics

- [x] 9.1 Implement `compute_calibration_metrics(y_true, prob_series)` in `bot/backtest/metrics.py` returning `{brier_score, calibration_bins}`
- [x] 9.2 Implement Brier score as `mean((prob - y)^2)` using only aligned rows where both `y_true` and `prob_series` are non-NaN
- [x] 9.3 Implement 10-bin reliability bins using `sklearn.calibration.calibration_curve`; omit empty bins from output dict
- [x] 9.4 Raise `ValueError` if `y_true.index` does not equal `prob_series.index`

## 10. Walk-Forward Summary Metrics

- [x] 10.1 Implement `compute_walkforward_summary(folds: list[dict]) -> dict` in `bot/backtest/metrics.py`
- [x] 10.2 Exclude folds with `None` metric values from all aggregate computations; set `n_folds` to count of non-None folds
- [x] 10.3 Compute `median_sharpe`, `std_sharpe`, `best_sharpe`, `worst_sharpe`, `median_total_return`, `median_max_drawdown`, `median_num_trades`, `median_win_rate`, `n_folds`

## 11. Optional Brier Score in compute_metrics

- [x] 11.1 Add `prob_series=None` parameter to `compute_metrics` in `bot/backtest/metrics.py`
- [x] 11.2 When `prob_series` is provided, call `compute_calibration_metrics` and include `brier_score` in the strategy metrics dict
- [x] 11.3 Verify `compute_metrics(results_df)` without `prob_series` returns the same dict as Phase 2 (no `brier_score` key)

## 12. Phase 3 Research Notebook

- [x] 12.1 Create `notebooks/phase3_robustness.ipynb` with section headers: Setup, Data (Multi-Symbol), Regime Features, Walk-Forward (Vol-Adjusted Labels), Walk-Forward (Regime Features), Walk-Forward Summary, Calibration Diagnostics, Kill Criterion Evaluation
- [x] 12.2 Section 1 (Setup): imports from `bot.*`; load credentials; define constants (SYMBOLS, fold geometry)
- [x] 12.3 Section 2 (Data): fetch BTC/USD, ETH/USD, SOL/USD 6-month hourly bars; call `compute_cross_asset_features`
- [x] 12.4 Section 3 (Regime Features): call `compute_features(df_btc, extended=True, regime=True)`; display feature stats and regime distribution
- [x] 12.5 Section 4 (Walk-Forward — Vol Labels): call `run_walkforward` on BTC/USD with `make_vol_adjusted_labels`; display per-fold results table
- [x] 12.6 Section 5 (Walk-Forward — Regime Features): re-run with regime features added; compare per-fold results to Section 4
- [x] 12.7 Section 6 (Walk-Forward Summary): call `compute_walkforward_summary` on all fold results; display median/std/best/worst Sharpe
- [x] 12.8 Section 7 (Calibration): call `compute_calibration_metrics` on test-fold probabilities; display Brier score and reliability table
- [x] 12.9 Section 8 (Kill Criterion): explicitly evaluate the acceptance gate — median OOS Sharpe > 0 across folds and ≥ 2 of 3 symbols — and print PASS or FAIL with evidence

## 13. Acceptance Criteria Verification

- [x] 13.1 Run `notebooks/phase3_robustness.ipynb` end-to-end with real Alpaca credentials and confirm no errors
- [x] 13.2 Confirm `compute_features(df, extended=True, regime=True)` returns 12 non-NaN feature columns
- [x] 13.3 Confirm `make_vol_adjusted_labels` returns a labeled fraction ≥ 20% on 6-month BTC/USD data
- [x] 13.4 Confirm `run_walkforward` produces exactly `WALKFORWARD_N_FOLDS` per-fold result dicts with all required keys
- [x] 13.5 Confirm `compute_walkforward_summary` output dict contains all 9 required keys
- [x] 13.6 Confirm `apply_signal_policy` with default parameters produces a valid integer signal series with no NaN
- [x] 13.7 Confirm `run_backtest(df)` without `policy_fn` produces results byte-for-byte identical to Phase 2 for the same input
- [x] 13.8 Confirm `compute_calibration_metrics` returns a Brier score in `[0.0, 1.0]` and non-empty calibration bins
- [x] 13.9 Confirm `python -m bot --strategy logreg` continues to work without modification (Phase 2 live bot unaffected)
- [x] 13.10 Evaluate and record the kill criterion result in the notebook: if median OOS Sharpe ≤ 0 across all symbols and folds, document as Phase 3 conclusion and halt further live deployment planning
