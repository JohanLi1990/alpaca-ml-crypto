## ADDED Requirements

### Requirement: Dry-run mode prevents order placement
When dry-run mode is enabled, the system SHALL NOT call any Alpaca order placement endpoint under any circumstance.

#### Scenario: Signal triggers no order in dry-run
- **WHEN** dry-run mode is enabled and a BUY or SELL signal is generated
- **THEN** no order is submitted to Alpaca and no order-related API call is made

#### Scenario: Signal logs intent in dry-run
- **WHEN** dry-run mode is enabled and a BUY or SELL signal is generated
- **THEN** the system logs that it would place an order but does not do so

### Requirement: Dry-run mode is enabled by default
The system SHALL default to dry-run mode so that accidental live execution is not possible without an explicit opt-in.

#### Scenario: Default behavior
- **WHEN** the application is run without any execution mode flag
- **THEN** dry-run mode is active and no orders can be placed

### Requirement: Dry-run mode is configurable via CLI flag or environment variable
The system SHALL allow dry-run mode to be explicitly set via a `--dry-run` / `--live` CLI flag or a `DRY_RUN` environment variable.

#### Scenario: Explicit dry-run flag
- **WHEN** the application is started with `--dry-run`
- **THEN** dry-run mode is active regardless of the environment variable value

#### Scenario: Explicit live flag
- **WHEN** the application is started with `--live`
- **THEN** dry-run mode is disabled (live execution mode is active)

#### Scenario: Environment variable override
- **WHEN** `DRY_RUN=true` is set in the environment and no CLI flag is given
- **THEN** dry-run mode is active
