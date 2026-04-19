## ADDED Requirements

### Requirement: Compute strategy returns from signals and bar returns
The system SHALL compute per-bar strategy returns as `signal_{t-1} * bar_return_t`, where `signal` is lagged by one bar to avoid look-ahead (the signal at bar `t` is based on information available after bar `t` closes, so it is applied to bar `t+1`).

#### Scenario: Signal applied to next bar return
- **WHEN** the backtest is run on a DataFrame with `signal` and `close` columns
- **THEN** each strategy return at row `t` equals `signal_{t-1}` multiplied by the bar return at `t`

#### Scenario: First bar has no prior signal
- **WHEN** the first bar is processed (no prior signal exists)
- **THEN** the strategy return for that bar is 0 (no position held)

### Requirement: Deduct transaction costs on position changes
The system SHALL subtract a flat transaction fee for each bar where the position changes. The fee SHALL be configurable (default: 0.002, i.e., 0.20% per trade). A position change is defined as `signal_t != signal_{t-1}`.

#### Scenario: Fee deducted on entry
- **WHEN** signal changes from `0` to `1` (position entry)
- **THEN** the transaction fee is subtracted from the strategy return for that bar

#### Scenario: Fee deducted on exit
- **WHEN** signal changes from `1` to `0` (position exit)
- **THEN** the transaction fee is subtracted from the strategy return for that bar

#### Scenario: No fee when holding
- **WHEN** the signal does not change between two consecutive bars
- **THEN** no transaction fee is subtracted

### Requirement: Compute cumulative equity curve
The system SHALL compute a cumulative equity curve for the strategy as `(1 + strategy_returns).cumprod()`, starting from a base of 1.0.

#### Scenario: Equity curve starts at 1.0
- **WHEN** the equity curve is computed
- **THEN** the first value equals 1.0 (or the first period return applied to 1.0)

#### Scenario: Equity curve is monotone-compounding
- **WHEN** all strategy returns are non-negative
- **THEN** the equity curve is non-decreasing

### Requirement: Compute buy-and-hold equity curve for comparison
The system SHALL compute a buy-and-hold equity curve over the same period as the strategy backtest using the same bar returns but with a constant long signal.

#### Scenario: Buy-and-hold baseline computed
- **WHEN** the backtest runs
- **THEN** a `bnh_equity` series is available representing continuous long exposure with no transaction costs
