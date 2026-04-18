## ADDED Requirements

### Requirement: Load API credentials from environment
The system SHALL load `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` from the process environment before making any Alpaca API calls.

#### Scenario: Both credentials present
- **WHEN** both `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are set in the environment
- **THEN** the system reads their values and proceeds without error

#### Scenario: API key missing
- **WHEN** `APCA_API_KEY_ID` is not set in the environment
- **THEN** the system raises an error with a message identifying the missing variable and exits before making any API call

#### Scenario: API secret missing
- **WHEN** `APCA_API_SECRET_KEY` is not set in the environment
- **THEN** the system raises an error with a message identifying the missing variable and exits before making any API call

### Requirement: Support .env file for local development
The system SHALL attempt to load a `.env` file from the working directory before reading environment variables, allowing local development without exporting credentials in the shell.

#### Scenario: .env file present
- **WHEN** a `.env` file exists in the working directory containing credential variables
- **THEN** those variables are loaded into the environment and used for the API client

#### Scenario: .env file absent
- **WHEN** no `.env` file exists
- **THEN** the system silently continues, relying on already-set environment variables

### Requirement: Credentials never logged
The system SHALL NOT write API key or secret values to any log output, stdout, or stderr at any log level.

#### Scenario: Startup log
- **WHEN** the application starts and credentials are loaded
- **THEN** the log confirms credentials were loaded (e.g., "Credentials loaded") without printing their values
