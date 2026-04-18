## ADDED Requirements

### Requirement: Emit one log line per processed bar
The system SHALL emit exactly one plain-text log line for each bar that has a computed signal.

#### Scenario: One line per bar
- **WHEN** signal generation completes for N bars
- **THEN** exactly N log lines are emitted to stdout (or the configured output stream)

### Requirement: Log line contains required fields
Each log line SHALL include the following fields in a fixed order: timestamp, close price, signal, zscore, rolling_mean, rolling_std.

#### Scenario: Field presence
- **WHEN** a log line is emitted
- **THEN** it contains timestamp, close, signal, zscore, rolling_mean, and rolling_std values

### Requirement: Consistent decimal precision in log output
Numeric values in log lines SHALL be formatted with fixed decimal precision to ensure consistent output across runs.

#### Scenario: Price precision
- **WHEN** close, rolling_mean, and rolling_std are logged
- **THEN** they are formatted to 2 decimal places

#### Scenario: Z-score precision
- **WHEN** zscore is logged
- **THEN** it is formatted to 4 decimal places

### Requirement: Dry-run mode is marked in log output
When the application runs in dry-run mode, each log line or the startup header SHALL include a visible DRY-RUN marker.

#### Scenario: Dry-run marker present
- **WHEN** dry-run mode is active and a log line is emitted
- **THEN** the line or the preceding startup line contains the text "DRY-RUN"

#### Scenario: No marker in live mode
- **WHEN** dry-run mode is not active
- **THEN** log lines do not contain the "DRY-RUN" marker
