## Context

Phases 2 and 3 ran logistic regression on 1-hour OHLCV bars across BTC/USD, ETH/USD, and SOL/USD. Both phases produced negative walk-forward OOS Sharpe ratios and near-random Brier scores (~0.25), indicating no durable predictive signal at hourly resolution with a linear classifier. Phase 4 targets the two highest-leverage root causes identified in the Phase 3 retrospective: (1) 1-hour bar noise — too short a horizon for structure to be learnable; (2) logistic regression linearity — cannot capture regime interactions like "high-vol + strong trend → continuation". Daily bars have a fundamentally higher signal-to-noise ratio and XGBoost natively captures non-linear feature interactions without feature-engineering them explicitly.

The Phase 3 walk-forward harness, abstain-band signal policy, and calibration diagnostics are proven and reusable. The entire Phase 4 change is a swap of two components (bar resolution + model class) while keeping the evaluation infrastructure identical. This minimizes new code surface and keeps the experiment controlled.

## Goals / Non-Goals

**Goals:**
- Fetch 2 years of daily OHLCV bars for BTC/USD, ETH/USD, SOL/USD via Alpaca
- Label each bar using a 5-day ATR-normalised forward return (same leakage-free contract as Phase 3 vol-adjusted labels, scaled to daily resolution)
- Adapt all feature engineering to daily lookback windows
- Train XGBoost classifier with time-series-safe hyperparameter search per fold
- Log per-fold SHAP feature importance so we can understand what the model is learning
- Reuse the Phase 3 walk-forward harness, signal policy, and calibration metrics unchanged
- Run the full experiment in `notebooks/phase4_daily_xgboost.ipynb`
- Apply the kill criterion: median OOS Sharpe > 0 on ≥2 of 3 symbols

**Non-Goals:**
- Updating the live bot to use XGBoost (only if kill criterion passes)
- Ensemble or stacking across multiple model classes
- Intraday features or order-book data
- Changing the walk-forward fold geometry (train/val/test bar counts scale by data availability but the harness logic is unchanged)

## Decisions

### Daily bar resolution over 4-hour

**Decision:** Use `TimeFrame.Day` (not `TimeFrame.Hour` × 4 or `TimeFrame.FourHour`).

**Rationale:** Daily bars provide a full market-session signal that integrates intraday noise. The 2-year lookback gives ~730 bars — enough for the walk-forward harness with train=400/val=100/test=100 and 3–4 folds. 4-hour bars would require a separate lookback calculation and window-size tuning without substantially changing the regime character.

**Alternative considered:** 4-hour bars — rejected because they have ~6× more rows (4320 vs 730) but roughly the same regime complexity, adding data-management complexity without a clear hypothesis advantage.

---

### XGBoost over other tree-based models

**Decision:** Use `xgboost.XGBClassifier` with `eval_metric="logloss"`, `use_label_encoder=False`.

**Rationale:** XGBoost is the most widely validated gradient-boosted tree library in quantitative finance. It natively handles the feature importance + SHAP workflow. LightGBM and CatBoost offer marginal differences for this dataset size; standardising on XGBoost keeps the dependency footprint minimal and SHAP integration straightforward.

**Alternative considered:** `sklearn.ensemble.GradientBoostingClassifier` — rejected because it lacks native SHAP support and is ~10× slower on comparable problems.

---

### SHAP via `shap.TreeExplainer` per fold

**Decision:** Compute mean absolute SHAP values across the test set for each fold and log them alongside fold metrics.

**Rationale:** The Phase 3 Fold 2 anomaly (positive Sharpe every symbol, negative elsewhere) suggests the model is picking up a regime-specific signal. SHAP values will reveal whether different features dominate in the positive vs negative folds, making the anomaly diagnosable.

**Alternative considered:** XGBoost native `feature_importances_` — rejected because it uses split-count importance which is biased toward high-cardinality features; SHAP is consistent across all feature types.

---

### Label horizon: 5-day forward return

**Decision:** Label each bar using the sign of the 5-day ATR-normalised forward return, with training-data quantile thresholds.

**Rationale:** 5-day (1-week) forward return is long enough to smooth daily noise but short enough that the market regime doesn't change between labeling and prediction. The ATR normalisation from Phase 3 is preserved so labels are volatility-calibrated. 

**Alternative considered:** 10-day or 20-day — rejected for now because they reduce the number of labeled bars significantly on a 730-bar dataset, potentially starving training folds.

---

### Adapted daily feature windows

**Decision:** Scale lookback windows proportionally from hourly to daily:
- Rolling std 20-bar (1h) → rolling std 5-bar (daily) for short-vol
- Vol percentile 252-bar (1h) → 60-bar (daily, ~3 months) for regime bucket
- Trend slope 24-bar (1h) → 10-bar (daily, 2 weeks)
- Lagged returns: lags 1, 2, 3 days
- Momentum: 5-day and 20-day returns
- Volume z-score: 5-day rolling window

**Rationale:** The hourly windows were calibrated for 1h bars. Proportional scaling to daily preserves the intended economic lookback (e.g., 252 1h bars ≈ ~10 weeks; 60 daily bars ≈ ~3 months — slightly longer but appropriate for daily regime detection).

## Risks / Trade-offs

**[Data sparsity] 730 daily bars is tight for 4 walk-forward folds.**  
→ Mitigation: Use train=400/val=100/test=100 geometry (600 per fold, 3-fold overlap = 900 bars needed for fold 3). With 730 bars, 3 folds are feasible; fold 4 will be skipped — same behaviour as Phase 3. Document in notebook.

**[XGBoost overfitting] Tree models can overfit aggressively on small datasets.**  
→ Mitigation: `max_depth` limited to [2, 3, 4], `subsample=0.8`, `colsample_bytree=0.8` in the grid search. TimeSeriesSplit with 3 inner folds. Early stopping evaluated but not required for a 2-year window.

**[SHAP computation time] TreeExplainer on 100-bar test set is fast (<1s) per fold.**  
→ No meaningful risk. Total SHAP overhead per symbol ≈ 3–5 seconds.

**[Daily bar incomplete-bar exclusion] Alpaca returns today's partial bar in day requests.**  
→ Mitigation: Preserve the Phase 1 `exclude_last_bar` convention; drop the final row before feature computation.

**[Feature leakage on vol-adjusted labels] ATR and forward return must only use training-window data for threshold computation.**  
→ Mitigation: `compute_thresholds=True` flow from Phase 3 is preserved unchanged; daily label function follows the same call contract.

## Open Questions

- Should the XGBoost grid include `n_estimators` as a tunable parameter, or fix at 300 with early stopping? (Current decision: fix at 200, grid on depth/lr/subsample — keeps search small and reproducible.)
- Should we include Bitcoin funding rate as an additional feature if a free source is available? (Deferred to Phase 5 if Phase 4 passes the kill criterion.)
