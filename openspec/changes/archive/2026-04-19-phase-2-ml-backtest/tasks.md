## 1. Dependencies & Config

- [x] 1.1 Add `scikit-learn` and `matplotlib` to `requirements.txt`
- [x] 1.2 Add `LOGREG_CONFIDENCE_THRESHOLD`, `HISTORY_MONTHS`, `MIN_BARS_HISTORY`, and `TRANSACTION_FEE` constants to `bot/config.py`
- [x] 1.3 Create `bot/models/` directory with a `.gitkeep` so the artifact directory exists but model files are not committed

## 2. Historical Data Pipeline

- [x] 2.1 Extend `fetch_bars()` in `bot/data/fetcher.py` to accept `timeframe` and optional `start`/`end` datetime parameters
- [x] 2.2 Add a `fetch_bars_range()` convenience function that defaults to the past `HISTORY_MONTHS` at `TimeFrame.Hour`
- [x] 2.3 Add minimum bar count validation for historical mode (500 bars) with a descriptive error message
- [x] 2.4 Verify Phase 1 `fetch_bars()` call signature and behavior is unchanged (no breaking change)

## 3. ML Feature Engineering

- [x] 3.1 Add `extended=False` parameter to `compute_features()` in `bot/features/rolling.py`
- [x] 3.2 Implement `return_lag1`, `return_lag2`, `return_lag3` columns when `extended=True`
- [x] 3.3 Implement `momentum_12h` column (sum of last 12 bar returns) when `extended=True`
- [x] 3.4 Implement `volume_zscore_20` column (20-bar z-score of volume) when `extended=True`
- [x] 3.5 Verify all extended features use only data at or before bar `t` (no leakage)
- [x] 3.6 Verify `compute_features(df)` with no `extended` argument still returns only the 4 Phase 1 columns

## 4. Target Labeling

- [x] 4.1 Create `bot/features/labeling.py` with a `make_labels(df, lower=None, upper=None, compute_thresholds=False)` function
- [x] 4.2 Implement forward return computation (`close.shift(-1)`) internal to `make_labels`; ensure it is not included in the output
- [x] 4.3 Implement quantile threshold computation from the input DataFrame's forward returns when `compute_thresholds=True`
- [x] 4.4 Implement binary labeling: `1` above upper threshold, `0` below lower threshold; drop the middle band
- [x] 4.5 Return `(X, y, lower_threshold, upper_threshold)` from `make_labels` when `compute_thresholds=True`, or `(X, y)` when thresholds are passed in
- [x] 4.6 Verify `X.index == y.index` and `y.isna().sum() == 0` in the output

## 5. Logistic Regression Model

- [x] 5.1 Create `bot/strategies/logreg.py` with a `LogRegStrategy` class (or module-level `generate_signals` function matching the strategy interface)
- [x] 5.2 Implement model loading from `bot/models/logreg.pkl` with a clear `FileNotFoundError` message if absent
- [x] 5.3 Implement `generate_signals(df)` that computes `P(label=1)` and returns signal `1` if above `LOGREG_CONFIDENCE_THRESHOLD`, else `0`
- [x] 5.4 Verify the signal column is present and contains no NaN values after `generate_signals` returns

## 6. Vectorized Backtesting Engine

- [x] 6.1 Create `bot/backtest/__init__.py` and `bot/backtest/engine.py`
- [x] 6.2 Implement `run_backtest(df, fee=TRANSACTION_FEE)` that computes bar returns, applies lagged signals, deducts fees on position changes, and returns a results DataFrame
- [x] 6.3 Include `strategy_return`, `strategy_equity`, `bnh_return`, and `bnh_equity` columns in the results DataFrame
- [x] 6.4 Verify fee is deducted only on bars where `signal_t != signal_{t-1}`

## 7. Performance Metrics

- [x] 7.1 Create `bot/backtest/metrics.py` with a `compute_metrics(results_df)` function
- [x] 7.2 Implement `total_return` as `equity_curve.iloc[-1] - 1.0`
- [x] 7.3 Implement annualized `sharpe_ratio` with `sqrt(8760)` annualization factor; return `0.0` on zero volatility
- [x] 7.4 Implement `max_drawdown` as `min((equity / equity.cummax()) - 1)`
- [x] 7.5 Implement `num_trades` (count of signal `0→1` transitions) and `win_rate`
- [x] 7.6 Return a `dict` with keys: `total_return`, `sharpe_ratio`, `max_drawdown`, `num_trades`, `win_rate`
- [x] 7.7 Compute and return the same metric set for buy-and-hold in a second dict

## 8. Strategy Selection in Live Bot

- [x] 8.1 Add `--strategy {zscore,logreg}` argument to `argparse` in `bot/main.py` with default `zscore`
- [x] 8.2 Route signal generation to `zscore.generate_signals` or `logreg.generate_signals` based on the flag
- [x] 8.3 Display the active strategy name in the startup banner
- [x] 8.4 Verify `--strategy zscore` produces identical output to current Phase 1 behavior

## 9. Research Notebook

- [x] 9.1 Create `notebooks/phase2_backtest.ipynb` with section headers: Data, Features, Labels, Train, Backtest, Metrics, Save Model
- [x] 9.2 Section 1 (Data): call `fetch_bars_range()` and display DataFrame shape and head
- [x] 9.3 Section 2 (Features): call `compute_features(df, extended=True)` and show feature summary stats
- [x] 9.4 Section 3 (Labels): call `make_labels` on the training split with `compute_thresholds=True`; show class distribution
- [x] 9.5 Section 4 (Train): run `GridSearchCV` with `TimeSeriesSplit`; print best C and CV F1 scores; evaluate on test split (classification report)
- [x] 9.6 Section 5 (Backtest): call `run_backtest` on the test split signals; display results DataFrame head
- [x] 9.7 Section 6 (Metrics): call `compute_metrics`; display strategy vs buy-and-hold comparison table
- [x] 9.8 Section 7 (Equity Curve): plot `strategy_equity` and `bnh_equity` on the same axes using matplotlib
- [x] 9.9 Section 8 (Save Model): `joblib.dump` the best estimator to `bot/models/logreg.pkl`; confirm file exists

## 10. Acceptance Criteria Verification

- [x] 10.1 Run the notebook end-to-end with real Alpaca credentials and confirm no errors
- [x] 10.2 Confirm the equity curve plot displays correctly in the notebook
- [x] 10.3 Confirm the metrics table shows Sharpe, max drawdown, total return, trade count, and win rate for both strategy and buy-and-hold
- [x] 10.4 Confirm `bot/models/logreg.pkl` is created and loadable after the notebook run
- [x] 10.5 Run `python -m bot --strategy logreg` and confirm it loads the model and generates signals without error
- [x] 10.6 Run `python -m bot --strategy zscore` and confirm Phase 1 behavior is fully preserved
