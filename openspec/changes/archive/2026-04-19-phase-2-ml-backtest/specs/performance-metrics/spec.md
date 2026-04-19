## ADDED Requirements

### Requirement: Compute total return
The system SHALL compute total return as the final equity curve value minus 1.0, expressed as a decimal.

#### Scenario: Total return computed
- **WHEN** `compute_metrics` is called with the strategy equity curve
- **THEN** `total_return` equals `equity_curve.iloc[-1] - 1.0`

### Requirement: Compute annualized Sharpe ratio
The system SHALL compute the annualized Sharpe ratio from strategy returns assuming zero risk-free rate. Annualization factor is `sqrt(24 * 365)` for hourly bars (crypto trades continuously).

#### Scenario: Sharpe ratio computed
- **WHEN** `compute_metrics` is called
- **THEN** `sharpe_ratio` equals `mean(strategy_returns) / std(strategy_returns) * sqrt(8760)`

#### Scenario: Zero volatility edge case
- **WHEN** all strategy returns are identical (zero volatility)
- **THEN** `sharpe_ratio` is returned as `0.0` without raising a division error

### Requirement: Compute maximum drawdown
The system SHALL compute maximum drawdown as the largest peak-to-trough decline in the equity curve, expressed as a decimal (e.g., -0.15 for -15%).

#### Scenario: Max drawdown computed
- **WHEN** `compute_metrics` is called
- **THEN** `max_drawdown` equals `min((equity / equity.cummax()) - 1)`

### Requirement: Compute trade statistics
The system SHALL compute the total number of trades (position entries) and win rate (fraction of trades where exit equity exceeds entry equity).

#### Scenario: Trade count computed
- **WHEN** `compute_metrics` is called
- **THEN** `num_trades` equals the number of bars where the signal changed from `0` to `1`

#### Scenario: Win rate computed
- **WHEN** `compute_metrics` is called
- **THEN** `win_rate` equals the fraction of completed trades (entry to exit) that produced a positive net return

### Requirement: Return metrics as a structured dict
The system SHALL return all metrics from `compute_metrics` as a plain Python `dict` with keys: `total_return`, `sharpe_ratio`, `max_drawdown`, `num_trades`, `win_rate`.

#### Scenario: Metrics dict structure
- **WHEN** `compute_metrics` returns
- **THEN** the returned dict contains exactly the keys: `total_return`, `sharpe_ratio`, `max_drawdown`, `num_trades`, `win_rate`

### Requirement: Compare strategy metrics to buy-and-hold
The system SHALL compute the same metric set for the buy-and-hold baseline and include it alongside strategy metrics in the output, enabling direct comparison.

#### Scenario: Benchmark metrics available
- **WHEN** `compute_metrics` is called with both strategy and buy-and-hold equity curves
- **THEN** a second dict with the same keys is returned representing buy-and-hold performance
