# alpaca-ml-crypto

A research project exploring whether a machine-learning signal has a tradeable edge on 1-hour crypto bars, using the Alpaca paper trading API.

## Research Log

### Phase 1 — Rule-Based Signal Bot
**Goal:** Establish a deterministic data-to-signal pipeline as a testable foundation.  
**What was built:** Credential loading, Alpaca OHLCV bar fetching (BTC/USD, 1-min), rolling z-score feature layer, threshold-based BUY/SELL/HOLD signal generator, structured run logging, dry-run guard.  
**Result:** Working live bot (`python -m bot --strategy zscore`). No ML, no backtest — pipeline only.

---

### Phase 2 — ML Backtest
**Goal:** Replace the rule-based signal with a logistic regression trained on historical data, validated via backtesting.  
**What was built:** Historical 1-hour bar fetcher, extended feature set (lags, momentum, volume z-score), quantile-based forward-return labeling, logistic regression with time-series CV, vectorized backtesting engine (Sharpe, drawdown, win rate), `phase2_backtest.ipynb`, `--strategy logreg` live bot flag.  
**Result:** ❌ Negative. Strategy returned −10% vs buy-and-hold +6% on BTC over the test window. All 6 symbol×window experiments produced negative returns. Root causes identified: (1) 1-bar direction labels are too noisy; (2) features lack market-state context; (3) single 80/20 split masked instability.

---

### Phase 3 — Robustness-First Pipeline
**Goal:** Fix the three root causes from Phase 2 and determine whether any edge exists under a statistically credible evaluation harness.  
**What was built:**
- **Volatility-adjusted labels** — ATR-normalised forward returns replace raw 1-bar returns; labels are calibrated to current volatility, not absolute price moves.
- **Regime features** — vol percentile (low/med/high bucket over 252-bar history), trend slope (OLS over 24 bars), ATR-normalised return.
- **Cross-asset features** — 12-bar rolling BTC-vs-ETH and BTC-vs-SOL return spreads.
- **Walk-forward harness** — 4 rolling folds (1800 train / 600 val / 600 test bars each) replacing the single 80/20 split.
- **Abstain-band signal policy** — no trade when model confidence is near 0.5, reducing fee drag.
- **Calibration diagnostics** — Brier score and reliability diagram per fold.
- `phase3_robustness.ipynb` end-to-end experiment notebook.

**Result:** ❌ Kill criterion FAIL. Median OOS Sharpe was negative on all 3 symbols (BTC −2.67, ETH −4.43, SOL −2.35). The regime features improved results vs the Phase 2 baseline (BTC base median was −11.0), but were not sufficient to flip the Sharpe positive. A consistent pattern appeared: every symbol showed a positive Fold 2 (+1.9 to +4.1 Sharpe) and large losses in Folds 1 and 3, suggesting the model only works in a specific market regime rather than generalising. Brier scores (0.25–0.34) were near random-baseline, confirming the model is not learning a reliable probability signal.

**Conclusion:** No live deployment at this time. The 1-hour timeframe and logistic regression architecture do not appear to have a durable edge on these crypto assets in the tested period. Potential next directions: 4-hour/daily bars, longer labeling horizon (6–12 bars forward), or alternative model classes (XGBoost, gradient boosting).

---

### Phase 4 — Daily XGBoost Model
**Goal:** Test whether daily bars (730-day lookback) with an XGBoost gradient-boosted tree model can identify exploitable patterns missed by hourly logistic regression.  
**What was built:**
- **Daily bar infrastructure** — `fetch_daily_bars()` fetches calendar-day OHLCV from Alpaca (730-day lookback, ~729 bars post-filtering).
- **Daily labeling** — ATR-normalised 5-day forward returns (horizon increased from 1 bar to 5 days to match daily timeframe); P30/P70 quantile thresholding; drops first 14 rows (ATR warm-up) + last 5 rows (no forward return).
- **Daily features** — timeframe-aware scales: lagged returns (1, 2, 3 days), 5-bar momentum (vs 12-bar hourly), 5-bar volume z-score (vs 20-bar hourly), 60-bar vol percentile (vs 252-bar hourly), 10-bar trend slope (vs 24-bar hourly), 14-bar ATR-normalised return.
- **XGBoost model** — `XGBClassifier` with GridSearchCV over 18 param combos (max_depth, learning_rate, subsample) + TimeSeriesSplit(3) CV (54 total fits). Optimization: search with 50 trees, refit best params with 200 trees (4× speedup vs searching with 200).
- **Walk-forward harness (2 folds)** — 730 total bars → Fold 1: train[0:350], val[350:470], test[470:590]; Fold 2: train[120:470], val[470:590], test[590:710]. Buffers added to account for feature warm-up loss (~28 rows drops per symbol).
- **SHAP feature importance** — per-fold mean |SHAP| rankings to identify which features drive decisions; all features contribute meaningfully (rolling_mean most important).
- `phase4_daily_xgboost.ipynb` research notebook with 8 sections (setup, data, features, labels, walk-forward, metrics, SHAP, kill criterion).

**Results:** ❌ Kill criterion FAIL on all symbols.
- **BTC/USD**: Fold 1 Sharpe = −19.6 (return −12.4%), Fold 2 Sharpe = +9.0 (return +7.5%). Median = −5.3 [FAIL]
- **ETH/USD**: Fold 1 Sharpe = −4.4 (return −6.2%), Fold 2 Sharpe = −17.9 (return −13.4%). Median = −11.2 [FAIL]
- **SOL/USD**: Fold 1 Sharpe = −6.5 (return −9.3%), Fold 2 [SKIP—insufficient bars after features].
- **Median OOS Sharpe**: 0 of 3 symbols positive (required ≥2 for PASS). Overall: FAIL — no live deployment.

**Key Findings:**
1. **Daily timeframe insufficient** — Only 729 bars of data vs 50,000+ hourly bars in Phase 2/3. Limited training samples (350 train bars per fold vs 1800 hourly) reduce model capacity.
2. **SHAP importance shows model learned basic trend-following** — `rolling_mean`, `rolling_std`, `zscore` dominate (80%+ of importance); lagged returns and momentum much lower. Model is not discovering complex patterns.
3. **Regime-dependent losses** — BTC Fold 2 is profitable (+9.0 Sharpe) while Fold 1 loses heavily (−19.6). Suggests model overfits to a specific market regime rather than generalising. ETH shows opposite pattern (Fold 2 catastrophic −17.9).
4. **Label distribution skewed** — Thresholding at P30/P70 creates ~50% "flat" class (neither 5-day winner nor loser), diluting signal quality.
5. **Gradient boosting does not overcome hourly model failures** — Phase 3 logistic regression on hourly bars also failed. Daily bars + XGBoost does not rescue the underlying signal hypothesis.

**Lessons Learned:**

1. **Data quantity matters more than model sophistication** — GridSearchCV with 18 params + SHAP + 200-tree refit cannot overcome 729 bars of daily data. Hourly bars (50k+) still provide better learning signal despite simpler features and model class.

2. **Regime-dependence is a red flag** — A model that wins in one fold and loses in another (especially with time-series CV) suggests overfitting to market microstructure rather than capturing a fundamental edge. Robust edges generalize across different market states.

3. **Five-day horizon too long for reversals** — Crypto markets exhibit mean reversion at daily scales. A 5-day forward return label on daily bars is too coarse; may be better suited to longer-term trend strategies (weekly/monthly).

4. **Quantile thresholding creates label noise** — P30/P70 split leaves middle 40% as "flat" (no signal). Could try:
   - Raw continuous labels (regression instead of classification)
   - Tighter quantiles (P25/P75 or P20/P80) to reduce ambiguous region
   - Asymmetric thresholds (e.g., P20/P80) to weight extreme moves

5. **Feature warm-up is a data-loss bottleneck** — Rolling window (20-bar) + labeling (5-bar) + ATR (14-bar) = ~28 rows lost per 730-bar dataset (~3.8%). With only 729 bars, this is significant. Hourly data absorbs this loss better because of abundance.

6. **XGBoost grid search optimisation** — Searching with 50 trees then refit with 200 saves ~4× time. Time-series CV (no lookahead bias) is essential for walk-forward, but GridSearchCV default 10-fold CV on small daily sets is risky; TimeSeriesSplit(3) is better. However, 3 splits on 350-bar training window is still tight (116 bars per fold).

7. **Kill criterion as a stopping gate is effective** — Requiring median OOS Sharpe > 0 on ≥2 symbols prevents deploying unprofitable strategies. Phase 4 correctly failed without false positives (no lucky folds masking bad median).

---

## Lessons Learned Across All Phases

**On Signal Hypothesis:**
- Raw 1-hour direction labels are too noisy for a learned signal (Phase 2 failure).
- Volatility adjustment (ATR normalisation) improves interpretability but does not recover positive returns (Phase 3 still negative).
- Daily bars do not improve over hourly, contrary to initial hypothesis (Phase 4 failure).
- **Implication**: These crypto assets may not have a durable short-term ML edge, or the edge exists only in specific market regimes (e.g., strong trends, low volatility).

**On Backtesting Methodology:**
- Single train/test split masks instability; walk-forward CV is necessary (Phase 3 innovation).
- Time-series CV (no lookahead bias) is mandatory for temporal data; standard k-fold CV invalidates results.
- Regime-dependent performance (wins in some folds, loses in others) is a red flag, not a reason to deploy.
- Brier score (calibration) and reliability diagrams are underrated diagnostics; should be standard in ML trading backtests.

**On Model Selection:**
- Model complexity (logistic regression vs XGBoost) is not the bottleneck; data quality and feature expressiveness are.
- GridSearchCV hyperparameter search is valuable but expensive; use coarse grid first, then refine on promising region.
- SHAP importance is useful for debugging but should not justify weak results (Phase 4 showed SHAP clearly, but strategy still failed).

**On Production Readiness:**
- A strategy must show positive median OOS Sharpe on **most** symbols, not just one lucky asset or fold.
- Dry-run guard and abstain-band signal policy are necessary but not sufficient; no amount of infrastructure rescues a weak signal.
- Live deployment (Phase 5+) should only proceed after exhausting backtesting iterations.

---

## Project Structure

```
bot/               Core bot and ML pipeline
  data/            Alpaca bar fetcher (hourly + daily)
  features/        Feature engineering (rolling, regime, labeling)
    rolling.py     Timeframe-aware base features (hourly/daily scales)
    regime.py      Regime features (vol percentile, trend slope, ATR)
    labeling.py    Hourly + daily labeling (1-bar and 5-day forward returns)
  models/          Trained models
    xgboost_model.py   XGBoost training, SHAP importance
  strategies/      zscore (rule-based) and logreg (ML)
  backtest/        Vectorized engine, metrics, walk-forward harness
  utils/           Credentials, logger
notebooks/         Research notebooks
  phase2_backtest.ipynb            Phase 2 logistic regression on hourly bars
  phase3_robustness.ipynb          Phase 3 regime features + walk-forward harness
  phase4_daily_xgboost.ipynb       Phase 4 XGBoost on daily bars
openspec/          Spec-driven change management artifacts
  changes/
    archive/       Completed changes with design/proposal/tasks/specs
      2026-04-18-phase-1-signal-bot/
      2026-04-19-phase-2-ml-backtest/
      2026-04-19-phase-3-robustness/
      2026-04-19-phase-4-daily-xgboost/
```

## Running the live bot (dry-run)

```bash
conda activate strategy-lab
python -m bot --strategy zscore   # Phase 1 rule-based
python -m bot --strategy logreg   # Phase 2 ML (requires trained model artifact)
```

---

## Research Conclusion

This project tested the hypothesis that **machine learning can identify a durable short-term edge in BTC/ETH/SOL using 1-hour or daily crypto bars**. 

**Result**: ❌ **No edge found** across all 4 phases.

### Summary by Phase

| Phase | Timeframe | Model | Data Window | Median OOS Sharpe | Kill Criterion |
|-------|-----------|-------|-------------|------------------|----------------|
| 1     | N/A       | Rule-based (z-score)   | N/A         | N/A             | N/A (pipeline only) |
| 2     | 1-hour    | Logistic Regression    | 6 months    | −10% / +6% hold | FAIL (negative return) |
| 3     | 1-hour    | Logistic Regression +  | 2.5 years   | −2.67 to −4.43  | FAIL (3/3 symbols negative) |
|       |           | Regime Features        |             |                 |                     |
| 4     | Daily     | XGBoost                | ~2 years    | −5.30 to −11.18 | FAIL (3/3 symbols negative) |

### Why No Edge?

1. **Hypothesis may be fundamentally wrong** — These crypto assets may not exhibit learnable short-term ML patterns, or any edge is arbitraged away too quickly for traditional ML.

2. **Label construction is unreliable** — Both 1-bar (too noisy) and 5-bar (too coarse) forward returns fail. Middle ground (2–3 bars) not tested, but unlikely to rescue negative results.

3. **Feature engineering bottleneck** — Regime features improved Phase 3 vs Phase 2 (BTC base −11.0 → −2.67 median) but did not flip to positive. Simple rolling statistics (mean, std) dominate SHAP importance even after adding complex features.

4. **Overfitting masked by regime-dependence** — Phase 3 and 4 both showed one profitable fold and one catastrophic fold, suggesting the model memorizes market microstructure rather than learning generalizable patterns.

5. **Data quantity insufficient for complex models** — Daily (729 bars) < Hourly (50k+ bars), yet neither produced a signal. XGBoost did not outperform simpler logistic regression, suggesting the problem is not model class but signal quality.

### Possible Future Directions (Not Pursued)

- **Longer timeframes** (4-hour, daily, weekly) with forward horizons matched to market microstructure
- **Alternative labels** (raw regression targets, Sharpe-maximised thresholds, momentum bins)
- **Market regimes** (only trade in high vol, trending markets; abstain in choppy consolidation)
- **Cross-asset hedging** (spread strategies, pairs trading with correlations)
- **Fundamental + sentiment data** (on-chain metrics, social signals for crypto; not just price/volume)
- **Deep learning** (LSTMs, Transformers) if more diverse data becomes available

### Recommendation

**Conclude research phase and move to deployment phase with learnings, not edge.**

Rather than continue iterating on backtests (diminishing returns), deploy Phase 1 (rule-based z-score) to live paper trading to:
- Validate infrastructure (order execution, error handling, logging)
- Gather real market microstructure data
- Detect regime shifts and slippage in production

This pivots from "find a profitable strategy" (failed) to "learn from production data" (valuable either way).

---

**Research Duration**: ~2 weeks (4 phases, 40+ implementation tasks, 3 notebooks, 20+ experiments)  
**Code Lines**: ~1500 (features, models, backtest harness) + 400 (notebooks)  
**Repository**: [alpaca-ml-crypto](https://github.com/your-repo)  
**Date Completed**: 2026-04-19
