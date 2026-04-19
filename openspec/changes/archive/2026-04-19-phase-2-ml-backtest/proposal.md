## Why

Phase 1 established a deterministic rule-based signal pipeline for BTC/USD. While useful as a foundation, rule-based z-score thresholds have no adaptive capacity — they cannot learn from market structure. Phase 2 introduces a machine learning layer (logistic regression) trained on historical data, validated through vectorized backtesting, so the strategy's edge can be measured before any live capital is deployed.

## What Changes

- Extend the bar fetcher to support configurable timeframes and date-range queries (required for historical training data)
- Extend feature computation to include momentum, lagged returns, and volume z-score (richer feature set for ML)
- Add target labeling using quantile-based forward-return thresholds (defines what the model learns to predict)
- Add logistic regression model training with time-ordered train/test split and regularization grid search
- Add a `logreg` strategy that loads a persisted model artifact and generates long/flat signals
- Add a vectorized backtesting engine that applies signals to historical returns with transaction cost deduction
- Add performance metrics computation (Sharpe ratio, max drawdown, total return, trade statistics)
- Add a research notebook that orchestrates the full pipeline: fetch → features → label → train → backtest → evaluate
- Extend the live bot entry point with a `--strategy` flag to select between `zscore` (Phase 1) and `logreg` (Phase 2)

## Capabilities

### New Capabilities

- `historical-data-pipeline`: Fetch and cache multi-month OHLCV bar history for a configurable symbol and timeframe (default: BTC/USD, 1-hour)
- `ml-feature-engineering`: Compute an enriched feature set including lagged returns, momentum, realized volatility, and volume z-score with strict leakage prevention
- `target-labeling`: Label each bar with a directional outcome (long / neutral) using quantile-based forward return thresholds computed on training data only
- `logreg-model`: Train, evaluate, and persist a logistic regression classifier; load it at inference time for live signal generation
- `vectorized-backtest`: Simulate strategy performance on held-out historical data, applying signals to bar returns with configurable transaction cost
- `performance-metrics`: Compute Sharpe ratio, maximum drawdown, total return, win rate, and trade count; compare against buy-and-hold benchmark
- `strategy-selection`: Allow the live bot to select between rule-based (`zscore`) and ML-based (`logreg`) strategies via a CLI flag

### Modified Capabilities

- `bar-fetching`: Add support for configurable `TimeFrame` parameter and explicit `start`/`end` date range (currently hard-coded to 1-minute, anchored to "now")
- `feature-computation`: Extend the feature set with momentum, lagged returns, and volume z-score columns while preserving all existing Phase 1 columns

## Impact

- **New dependencies**: `scikit-learn`, `matplotlib` (equity curve plotting in notebook)
- **New modules**: `bot/features/labeling.py`, `bot/strategies/logreg.py`, `bot/backtest/engine.py`, `bot/backtest/metrics.py`, `bot/models/` (artifact directory)
- **New entry point**: `notebooks/phase2_backtest.ipynb`
- **Modified modules**: `bot/data/fetcher.py` (timeframe + date range), `bot/features/rolling.py` (additional features), `bot/config.py` (new constants), `bot/main.py` (`--strategy` flag)
- **Phase 1 unchanged**: `bot/strategies/zscore.py` and all Phase 1 behavior is fully preserved
- **No order placement**: live order execution remains out of scope
