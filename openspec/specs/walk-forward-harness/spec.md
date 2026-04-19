## ADDED Requirements

### Requirement: Execute rolling walk-forward folds with non-overlapping test windows
`run_walkforward` SHALL step through the input DataFrame in rolling windows defined by `train_bars`, `val_bars`, and `test_bars`. Each fold advances the start of the test window by `test_bars`, producing non-overlapping OOS test periods.

#### Scenario: Walk-forward produces N non-overlapping test windows
- **WHEN** `run_walkforward(df, n_folds=4, train_bars=1800, val_bars=600, test_bars=600, ...)` is called
- **THEN** exactly 4 folds are produced, each with a test window starting `test_bars` after the previous fold's test window start

#### Scenario: Train and validation data never overlap with test data
- **WHEN** a fold is evaluated
- **THEN** train and validation bars precede the test window start index with no shared rows

### Requirement: Accept feature, label, model, and policy functions as callables
`run_walkforward` SHALL accept `feature_fn`, `label_fn`, `model_fn`, and `policy_fn` as callable arguments. Each fold applies these functions in sequence: `feature_fn(df_train)` → `label_fn(X_train)` → `model_fn(X_labeled, y_labeled)` → `policy_fn(prob_series)` → backtest.

#### Scenario: Custom feature function applied per fold
- **WHEN** a `feature_fn` callable is provided
- **THEN** it is called with the training slice of the raw DataFrame for each fold, and its output is passed to `label_fn`

#### Scenario: Model trained fresh on each fold
- **WHEN** each fold executes
- **THEN** `model_fn` is called with the labeled training data for that fold, and returns a fitted model without any state carried over from prior folds

### Requirement: Return a list of per-fold result dicts
`run_walkforward` SHALL return a `list[dict]`, where each dict contains per-fold metrics: `fold`, `train_start`, `train_end`, `test_start`, `test_end`, `total_return`, `sharpe_ratio`, `max_drawdown`, `num_trades`, `win_rate`, `brier_score`.

#### Scenario: Per-fold result dict structure
- **WHEN** `run_walkforward` returns
- **THEN** each dict in the result list contains all the keys: `fold`, `train_start`, `train_end`, `test_start`, `test_end`, `total_return`, `sharpe_ratio`, `max_drawdown`, `num_trades`, `win_rate`, `brier_score`

#### Scenario: Fold results are ordered chronologically
- **WHEN** examining the returned list
- **THEN** fold 1 covers earlier dates than fold 2, and so on

### Requirement: Aggregate walk-forward folds into summary statistics
`compute_walkforward_summary` SHALL accept the per-fold list from `run_walkforward` and return a dict with aggregate statistics: `median_sharpe`, `std_sharpe`, `best_sharpe`, `worst_sharpe`, `median_total_return`, `median_max_drawdown`, `median_num_trades`, `median_win_rate`, `n_folds`.

#### Scenario: Summary statistics computed correctly
- **WHEN** `compute_walkforward_summary(folds)` is called with 4 fold dicts
- **THEN** `median_sharpe` equals the median of the 4 `sharpe_ratio` values and `n_folds` equals 4

### Requirement: Skip failing folds and continue
If a single fold raises an exception (e.g., insufficient labeled bars), `run_walkforward` SHALL log a warning, record `None` for that fold's metrics, and continue with the remaining folds.

#### Scenario: Failing fold does not abort the harness
- **WHEN** one fold's label function returns fewer than the minimum required labeled rows
- **THEN** that fold is skipped with a warning and the remaining folds complete normally

### Requirement: No leakage across folds
The walk-forward harness SHALL ensure that no information from a fold's validation or test window is used during training of that fold. Thresholds, scalers, and model parameters MUST be derived exclusively from training data within each fold.

#### Scenario: Label thresholds recomputed per fold from training data
- **WHEN** a fold executes
- **THEN** quantile thresholds for labeling are computed from the training split of that fold only, not from the full dataset
