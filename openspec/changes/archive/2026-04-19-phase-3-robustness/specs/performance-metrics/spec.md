## ADDED Requirements

### Requirement: Compute Brier score as part of compute_metrics output
`compute_metrics` SHALL accept an optional `prob_series` parameter alongside the existing `results_df`. When provided, it calls `compute_calibration_metrics(y_true, prob_series)` and includes `brier_score` in the returned strategy metrics dict.

#### Scenario: Brier score included when prob_series provided
- **WHEN** `compute_metrics(results_df, prob_series=prob_series)` is called
- **THEN** the strategy metrics dict includes the key `brier_score` as a float

#### Scenario: Brier score absent when prob_series not provided
- **WHEN** `compute_metrics(results_df)` is called without `prob_series`
- **THEN** the strategy metrics dict does not include `brier_score` (Phase 2 behavior preserved)

### Requirement: Provide compute_walkforward_summary to aggregate per-fold metrics
The system SHALL expose `compute_walkforward_summary(folds: list[dict]) -> dict` in `bot/backtest/metrics.py`. It SHALL compute aggregate statistics across fold dicts returned by `run_walkforward`.

#### Scenario: Median Sharpe aggregated
- **WHEN** `compute_walkforward_summary(folds)` is called with N fold dicts
- **THEN** `median_sharpe` equals the median of all non-None `sharpe_ratio` values across folds

#### Scenario: None folds excluded from aggregation
- **WHEN** one fold dict has `sharpe_ratio: None` (skipped fold)
- **THEN** it is excluded from all aggregate computations, and `n_folds` reflects the count of non-None folds

#### Scenario: Summary dict structure
- **WHEN** `compute_walkforward_summary` returns
- **THEN** the dict contains: `median_sharpe`, `std_sharpe`, `best_sharpe`, `worst_sharpe`, `median_total_return`, `median_max_drawdown`, `median_num_trades`, `median_win_rate`, `n_folds`
