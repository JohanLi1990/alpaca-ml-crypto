## Context

Phase 2 built a solid ML pipeline (fetch → features → labels → logistic regression → vectorized backtest) and ran a multi-symbol, multi-window robustness sweep. The result was consistently negative: test total return ranged from -15% to 0%, with most windows producing either zero trades (model too conservative) or active trading with strongly negative Sharpe (fees > edge). Classification accuracy was 52% — statistically indistinguishable from chance.

Phase 3 treats this as a clean diagnosis problem. The Phase 2 pipeline is kept intact as infrastructure; what changes is the *quality* of the signal on three axes: what the model is asked to predict (labels), what information it has access to (features), and how signal quality is measured (evaluation).

The primary constraint remains **no leakage**: all features and labels use only information available at the close of bar `t`. The secondary constraint is **falsifiability**: Phase 3 must define a crisp acceptance gate — positive median OOS Sharpe across walk-forward folds — so failure is detectable and not rationalized away.

## Goals / Non-Goals

**Goals:**
- Replace 1-bar direction labels with volatility-adjusted labels using ATR normalization (return / ATR), so the model learns to predict moves that are large relative to prevailing volatility
- Add regime features (realized vol percentile bucket, trend slope, ATR-normalized return) and cross-asset features (BTC/ETH/SOL relative return spread) to give the model signals that vary by market state
- Build a walk-forward harness that steps through time with rolling train/validate/test windows and reports per-fold and aggregate OOS metrics
- Add a cost-aware signal policy layer (abstain band, minimum hold bars) to structurally reduce unnecessary churn
- Add probability calibration diagnostics (Brier score, reliability diagram) to separate prediction quality from trading quality
- Produce a `notebooks/phase3_robustness.ipynb` that orchestrates the full Phase 3 research pipeline
- Define and enforce a kill criterion: if median OOS Sharpe remains ≤ 0 across the full walk-forward after feature improvements, document the finding and halt (do not proceed to live deployment)

**Non-Goals:**
- Long-short signals (long-only; shorts deferred)
- Replacing logistic regression with tree-based or neural models (deferred; linear model is not yet the bottleneck)
- Live order placement or automated retraining scheduler
- Multi-timeframe models (1-hour bars only; timeframe search deferred)
- Walk-forward retraining in the live bot (the bot still loads a single static model artifact)
- Position sizing or portfolio allocation across symbols

## Decisions

### D1: ATR-normalized forward return as the primary label

**Chosen**: Compute `forward_return_t / ATR_t` where ATR is the 14-bar average true range computed on close-to-close returns (leakage-free). Label bar `t` as `1` if the normalized move exceeds the 70th percentile of the training distribution; label `0` if below the 30th; exclude the middle 40%.

**Rationale**: Phase 2's failure pattern — many "long" trades that each earn a tiny return, then get wiped by fees — suggests the model was trying to predict noise. ATR-normalized labels filter out bars where the forward move is large in absolute terms but small relative to volatility. This aligns what the model learns to predict with what is tradeable after cost.

**Alternative considered**: Triple-barrier labeling (up barrier, down barrier, time barrier) — more sophisticated but requires a barrier width hyperparameter that is hard to set without overfitting. ATR normalization achieves similar volatility adjustment with no new hyperparameter.

---

### D2: Regime and cross-asset features computed in a new `bot/features/regime.py` module

**Chosen**: New module `bot/features/regime.py` with two functions:
- `compute_regime_features(df)`: adds `vol_percentile` (rolling 252-bar percentile of realized vol), `trend_slope` (OLS slope of close over 24 bars, normalized by rolling std), `atr_normalized_return` (bar return / 14-bar ATR)
- `compute_cross_asset_features(dfs: dict[str, DataFrame])`: takes a dict of `{symbol: df}` aligned by timestamp, adds `btc_excess_return_vs_eth`, `btc_excess_return_vs_sol` as relative return spreads over 12 bars

**Rationale**: Isolating regime and cross-asset feature computation in its own module preserves the existing `rolling.py` contract and makes the new features optional in any pipeline that doesn't have multi-symbol data. The two functions have different input signatures (single vs. multi-df), so co-location in one module is cleaner than splitting further.

**Alternative considered**: Add regime features directly to `rolling.py` under `extended=True` — rejected because cross-asset features require a multi-symbol fetch that the single-df API cannot accommodate without a breaking change.

---

### D3: Walk-forward harness as a standalone module in `bot/backtest/walkforward.py`

**Chosen**: `run_walkforward(df, n_folds, train_bars, val_bars, test_bars, feature_fn, label_fn, model_fn, policy_fn)` returns a list of per-fold result dicts. A companion `compute_walkforward_summary(folds)` aggregates into median/std/best/worst. The harness is fully self-contained: it accepts functions rather than hardcoded strategies, so it can be reused for any combination of features and models.

**Rationale**: A function-composition API avoids coupling the walk-forward engine to specific feature or label implementations. This makes it straightforward to run Phase 3 experiments in the notebook by passing different `feature_fn` callables.

**Alternative considered**: Implementing walk-forward inline in the notebook — rejected because it would be non-reusable and hard to debug. Putting it in `bot/backtest/walkforward.py` makes it importable from the live bot's research tooling in future phases.

---

### D4: Cost-aware signal policy as a thin wrapper, not a change to backtest engine internals

**Chosen**: Add `apply_signal_policy(prob_series, abstain_lo, abstain_hi, min_hold_bars)` in a new small function (in `bot/backtest/engine.py` or a separate `bot/backtest/policy.py`). The function takes raw model probabilities and returns a discrete signal series that has the abstain band and cooldown applied. The backtest engine receives the *output* signal and remains unchanged.

**Rationale**: Keeping the policy separate from the engine preserves the Phase 2 backtest contract (`run_backtest` takes a signal column, not probabilities). The policy layer becomes an explicit, testable step between model output and backtest input.

**Alternative considered**: Passing `abstain_threshold` directly into `run_backtest` — rejected because it entangles probability thresholding with return simulation, making it harder to compare policy variants.

---

### D5: Brier score and reliability diagram in `bot/backtest/metrics.py`

**Chosen**: Add `compute_calibration_metrics(y_true, prob_series)` returning `brier_score` (scalar) and `calibration_bins` (dict of bin center → mean predicted prob / fraction positives). Use `sklearn.calibration.calibration_curve` which is already available in the environment.

**Rationale**: Brier score measures probability accuracy independent of the classification threshold used for trading. A low Brier score with positive OOS Sharpe is a strong robustness signal. A high Brier score means the model's probabilities cannot be trusted even if a lucky threshold performs well in-sample. Adding it alongside existing metrics adds no new dependency and provides a key diagnostic.

**Alternative considered**: Reporting log-loss only — Brier score is more interpretable and bounded [0, 1], making it easier to compare across symbols and folds.

---

### D6: Walk-forward fold geometry: 4 folds × (train=1800, val=600, test=600) bars

**Chosen**: For a 6-month hourly dataset (~4300 bars), use 4 non-overlapping train/val/test triplets stepped forward by `test_bars` each time. This yields ~4 × 600 = 2400 OOS test bars and leaves ~1800-bar training windows that are large enough for logistic regression to converge. The notebook configures this via constants, not hardcoded values.

**Rationale**: 1800 train bars ≈ 75 days of hourly data — sufficient for logistic regression with ≤ 15 features. 600 bar test windows ≈ 25 days — long enough to see multiple trade cycles. 4 folds gives a meaningful median without running out of data.

**Alternative considered**: Expanding window (train always starts at bar 0, test window steps forward) — provides more training data per fold but makes fold test periods correlated with each other. Rolling window is cleaner for measuring non-stationary behavior.

---

### D7: Notebook as orchestration-only; all new logic lives in `bot/`

Preserved from Phase 2. `notebooks/phase3_robustness.ipynb` calls functions from `bot.features.regime`, `bot.backtest.walkforward`, `bot.backtest.metrics`, and `bot.features.labeling`. No business logic in notebook cells.

## Risks / Trade-offs

- **ATR normalization removes too many labels** → Mitigation: monitor labeled fraction after filtering; if it drops below 20% of bars, loosen the quantile cutoffs (e.g., 25/75 instead of 30/70). Document in notebook.
- **Cross-asset features require simultaneous multi-symbol fetch** → Mitigation: `compute_cross_asset_features` accepts pre-fetched aligned DataFrames; the notebook fetches all three symbols upfront. Alignment is by timestamp index, not integer position.
- **Walk-forward fold count too low for stable median estimates** → Mitigation: 4 folds is the minimum with 6 months of data. If variance across folds is very high (std > 2× median), the design doc should record this and Phase 4 should fetch 12 months. Document threshold in notebook.
- **Abstain band overfitting on validation** → Mitigation: fix the abstain band at `[0.45, 0.55]` by default; only allow one additional hyperparameter sweep (min hold bars) on the validation set. Do not tune both simultaneously.
- **Kill criterion subjectivity** → Mitigation: define the gate precisely in the acceptance criteria: median OOS Sharpe > 0 across all folds and at least 2 of 3 symbols. No partial credit.
- **Phase 2 live bot behavior unchanged** → No risk; new modules are additive and the live bot only loads `bot/models/logreg.pkl` with the existing interface.

## Open Questions

- Should the cross-asset features use raw return spread or beta-adjusted spread? Beta adjustment requires a rolling regression, adding complexity. Start with raw spread; revisit if it explains variance in residuals.
- Should walk-forward retraining be wired into the live bot in Phase 4, or is Phase 4 a different model class (e.g., gradient boosting)? Leave open — the answer depends on Phase 3 results.
