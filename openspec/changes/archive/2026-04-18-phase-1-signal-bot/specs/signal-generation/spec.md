## ADDED Requirements

### Requirement: Generate BUY/SELL/HOLD action signals
The system SHALL assign an action signal to each bar based on its z-score value. The signal vocabulary is BUY, SELL, and HOLD.

#### Scenario: BUY signal
- **WHEN** a bar's `zscore` is strictly greater than the upper threshold (default: 1.0)
- **THEN** the signal for that bar is BUY

#### Scenario: SELL signal
- **WHEN** a bar's `zscore` is strictly less than the lower threshold (default: -1.0)
- **THEN** the signal for that bar is SELL

#### Scenario: HOLD signal
- **WHEN** a bar's `zscore` is greater than or equal to the lower threshold and less than or equal to the upper threshold
- **THEN** the signal for that bar is HOLD

### Requirement: Signal thresholds are configurable
Upper and lower z-score thresholds SHALL be defined in a fixed configuration location (e.g., config file or constants module) so they can be changed without modifying signal logic.

#### Scenario: Threshold change
- **WHEN** the upper threshold is changed from 1.0 to 1.5 in the config
- **THEN** BUY signals are only generated for z-scores above 1.5 with no code changes in the signal function

### Requirement: Signal generation is deterministic
Given identical input feature values, the system SHALL always produce the same signal output.

#### Scenario: Reproducibility
- **WHEN** the same DataFrame with the same feature values is passed to signal generation twice
- **THEN** the `signal` column produced is identical in both runs

### Requirement: Signal generation handles at least 100 bars
The signal engine SHALL process a minimum of 100 fully-featured bars without error.

#### Scenario: 100-bar run
- **WHEN** a DataFrame with exactly 100 rows of complete features is passed to signal generation
- **THEN** all 100 rows receive a signal value and no errors are raised
