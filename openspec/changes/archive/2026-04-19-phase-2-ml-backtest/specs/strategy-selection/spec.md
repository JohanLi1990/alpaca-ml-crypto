## ADDED Requirements

### Requirement: Select strategy via CLI flag
The live bot entry point SHALL accept a `--strategy` CLI argument with allowed values `zscore` (default) and `logreg`. The selected strategy SHALL determine which signal generation module is invoked.

#### Scenario: Default strategy is zscore
- **WHEN** the bot is run without `--strategy`
- **THEN** the `zscore` rule-based strategy is used, preserving Phase 1 behavior

#### Scenario: Explicit zscore selection
- **WHEN** `--strategy zscore` is passed
- **THEN** the Phase 1 z-score threshold strategy generates signals

#### Scenario: LogReg strategy selected
- **WHEN** `--strategy logreg` is passed
- **THEN** the logistic regression model is loaded and used for signal generation

#### Scenario: Invalid strategy rejected
- **WHEN** an unrecognized value is passed to `--strategy`
- **THEN** argparse raises an error listing the valid options before any data is fetched

### Requirement: Strategy selection shown in startup banner
The startup banner SHALL display the active strategy name alongside the existing symbol, timeframe, and dry-run status fields.

#### Scenario: Strategy name in banner
- **WHEN** the bot starts with any strategy
- **THEN** the startup banner includes a line identifying the active strategy (e.g., `Strategy: logreg`)

### Requirement: Each strategy conforms to a common interface
All strategy modules SHALL expose a `generate_signals(df: DataFrame) -> DataFrame` function that accepts a feature DataFrame and returns the same DataFrame with a `signal` column added. The signal vocabulary MAY differ by strategy but must not break the pipeline contract.

#### Scenario: Zscore strategy interface preserved
- **WHEN** `generate_signals(df)` is called on the `zscore` strategy
- **THEN** the returned DataFrame has a `signal` column with string values `BUY`, `SELL`, or `HOLD`

#### Scenario: LogReg strategy interface compatible
- **WHEN** `generate_signals(df)` is called on the `logreg` strategy
- **THEN** the returned DataFrame has a `signal` column with integer values `1` (long) or `0` (flat)
