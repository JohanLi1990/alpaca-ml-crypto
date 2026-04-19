## Context

Phase 1 delivered a working rule-based signal pipeline: credentials → fetch → features → signals → log. The pipeline is deterministic, reproducible, and organized into purpose-aligned subpackages (`bot/data`, `bot/features`, `bot/strategies`, `bot/utils`). Phase 2 extends this foundation by replacing the rule-based signal source with a trained logistic regression model, adding a backtesting layer to validate the strategy on held-out data, and providing a Jupyter notebook as the research artifact.

The primary constraint is **no leakage**: every feature and label must use only information available at the close of bar `t`. The secondary constraint is **readability**: each new module has one clear responsibility and stays small.

## Goals / Non-Goals

**Goals:**
- Extend the fetcher to retrieve months of historical OHLCV bars at configurable timeframe (default 1-hour)
- Compute a richer feature set (7 features) that a logistic regression can meaningfully separate
- Label each bar with a binary outcome derived from quantile thresholds computed on training data only
- Train a logistic regression with time-ordered split and regularization grid search
- Run a vectorized backtest (signals → returns → equity curve) with transaction cost subtraction
- Compute Sharpe ratio, max drawdown, total return, win rate, and compare to buy-and-hold
- Persist the trained model so the live bot can load it at runtime
- Allow `--strategy zscore` vs `--strategy logreg` selection in the live bot entry point
- Produce a single notebook that runs the full research pipeline end-to-end

**Non-Goals:**
- Walk-forward retraining or online learning (deferred to Phase 3)
- Long-short signals (long-only in Phase 2; shorts deferred)
- Multi-symbol or multi-timeframe portfolio optimization
- Live order placement
- Model serving infrastructure (no API, no scheduler)
- Advanced risk engine or position sizing

## Decisions

### D1: 1-hour bars for training and inference

**Chosen**: `TimeFrame.Hour` for all Phase 2 data.

**Rationale**: 1-minute bars carry significant microstructure noise (bid-ask bounce, tick-level order flow) that a linear model cannot reliably separate from signal. Hourly bars smooth this noise while preserving 24 bars/day cadence on a 24/7 crypto market — a realistic day-trading frequency. Phase 1's 1-minute live signal bot is unaffected; the two strategies operate at different timeframes.

**Alternative considered**: 15-minute bars — reasonable, but 1-hour is the recommended starting point given logistic regression's linear decision boundary.

---

### D2: Quantile-based forward-return thresholds for target labeling

**Chosen**: Compute the 30th and 70th percentiles of the forward return distribution on training data only. Bars above P70 are labeled `1` (long), bars below P30 are labeled `0` (flat/skip), and the middle 40% is excluded from both training and evaluation.

**Rationale**: Fixed percentage thresholds (e.g., ±0.3%) become stale across volatility regimes. Quantile thresholds self-calibrate: during high-volatility periods the threshold widens; during calm periods it narrows. Crucially, the 70/30 split guarantees balanced class counts, which is important for logistic regression convergence and avoids silent accuracy inflation from a majority-class bias.

**Alternative considered**: Binary direction (up vs. down, 50/50 split) — simpler, but includes too many marginal moves as signal. Threshold-based labeling produces fewer but cleaner trades, which matters when transaction costs are ~0.20% per round trip.

---

### D3: 7-feature set: lags, momentum, volatility, volume z-score

**Chosen**: Compute at bar `t` (all use only `t` and earlier):
- `return_lag1`, `return_lag2`, `return_lag3`: last 3 hourly returns (autocorrelation)
- `momentum_12h`: sum of last 12 returns (half-day trend)
- `rolling_std_20`: realized volatility over 20 bars (vol regime)
- `zscore_20`: z-score of close over 20 bars (mean reversion; reused from Phase 1)
- `volume_zscore_20`: z-score of volume over 20 bars (unusual activity)

**Rationale**: 7 features covering 3 distinct phenomena (momentum, volatility, volume) provides logistic regression with orthogonal signal dimensions without risking multicollinearity explosion. Adding more features increases regularization sensitivity without meaningful gain at this model complexity.

**Alternative considered**: Including raw price level, VWAP, or RSI — rejected because price levels are non-stationary and RSI is a nonlinear transformation of returns (already captured by lags + zscore).

---

### D4: Simple 80/20 time-ordered split, no shuffling

**Chosen**: First 80% of sorted bars → training set. Last 20% → test set. No random shuffling.

**Rationale**: Financial time series have temporal dependence. Random shuffling causes look-ahead leakage: the model sees future bars during training. A time-ordered split simulates the real deployment condition (train on the past, evaluate on unseen future).

**Alternative considered**: Walk-forward cross-validation — more realistic but significantly more complex to implement and explain. Deferred to Phase 3.

---

### D5: Logistic regression with L2 regularization, grid search over C

**Chosen**: `sklearn.linear_model.LogisticRegression` with `solver='lbfgs'`, `class_weight='balanced'`, and grid search over `C ∈ [0.01, 0.1, 1.0, 10.0]` scored on F1.

**Rationale**: L2 regularization prevents overfitting on the 7-feature input. `class_weight='balanced'` handles any residual class imbalance after quantile filtering. F1 scoring balances precision and recall — relevant because both false positives (missed trades) and false negatives (bad trades) incur cost. `lbfgs` converges reliably on small feature sets.

**Alternative considered**: `LogisticRegressionCV` — uses built-in cross-validation but applies it with random folds by default, which risks leakage. Explicit `GridSearchCV` with `TimeSeriesSplit` is cleaner and more auditable.

---

### D6: Vectorized backtesting in pure pandas (no external library)

**Chosen**: `strategy_return_t = signal_{t-1} * bar_return_t - fee * |signal_t - signal_{t-1}|` computed as pandas series operations.

**Rationale**: For a long-flat strategy, the backtest is a single vector multiply and a fee deduction on position changes. No loop, no state machine, no external dependency. Transparent, fast, and readable. The equity curve is `(1 + strategy_returns).cumprod()`.

**Alternative considered**: `vectorbt` or `backtrader` — powerful but heavyweight. Introducing a backtesting framework at this stage would add a major dependency before the basic math has been validated. Keep it simple for Phase 2.

---

### D7: Model artifact persisted to `bot/models/logreg.pkl`

**Chosen**: `joblib.dump(model, "bot/models/logreg.pkl")` at end of notebook. Live bot calls `joblib.load(...)` in `bot/strategies/logreg.py` constructor.

**Rationale**: Decouples research (notebook trains and saves) from production (bot loads and uses). The `bot/models/` directory is gitignored so binary artifacts don't pollute version history. Joblib is already available via scikit-learn.

**Alternative considered**: Pickle directly — joblib is preferred for numpy arrays and sklearn estimators (better compression, safer deserialization).

---

### D8: Notebook is orchestration only; logic lives in `bot/`

**Chosen**: The notebook imports from `bot.*` and calls thin functions. No business logic implemented inline in notebook cells.

**Rationale**: Keeps the notebook readable (each cell is 5-10 lines). Logic in `bot/` is importable, testable, and reusable by the live bot. Avoids the "1000-line notebook mess" pattern.

---

### D9: `--strategy` CLI flag routes between zscore and logreg

**Chosen**: `python -m bot --strategy zscore` (default, Phase 1 behavior) or `--strategy logreg` (Phase 2, loads model). Strategy selection is additive — no existing code changes behavior.

**Rationale**: Explicit opt-in to the ML strategy prevents accidental live use of an untrained model. The default remains the deterministic Phase 1 strategy until the user has validated the model.

## Risks / Trade-offs

- **Label leakage** → Mitigation: quantile thresholds computed on training split only; test split uses training-derived thresholds. Enforced in `labeling.py` API design (thresholds passed in, not recomputed).
- **Survivorship bias in 6-month window** → Mitigation: acknowledged limitation; walk-forward retraining (Phase 3) addresses this. Document in notebook.
- **Model file not found at live bot startup** → Mitigation: `logreg.py` raises a clear `FileNotFoundError` with instructions to run the notebook if `logreg.pkl` is absent.
- **Backtest overfitting on test set** → Mitigation: test set is evaluated exactly once at the end of the notebook. No parameter tuning occurs after the test set is touched.
- **Transaction cost model simplification** → Mitigation: flat 0.20% per trade is conservative (Alpaca crypto fee is ~0.15%). Documented assumption in notebook.
- **1-hour signal cadence vs. Phase 1 1-minute cadence** → No conflict: strategies use different timeframes and are selected explicitly. Phase 1 live bot behavior unchanged.
