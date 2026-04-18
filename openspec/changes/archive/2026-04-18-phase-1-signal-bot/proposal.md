## Why

Alpaca supports crypto trading via a Python client but lacks any tooling for systematic signal generation. Phase 1 establishes a deterministic, reproducible data-to-signal pipeline for BTC/USD so we have a testable foundation before introducing machine learning in later phases.

## What Changes

- Add credential loading from environment variables (API key + secret)
- Add OHLCV bar fetching for BTC/USD via the Alpaca data API, excluding the last incomplete bar
- Add a pandas DataFrame normalization layer with explicit column types and UTC timestamps
- Add a rolling statistics feature layer (mean, std, z-score, returns)
- Add a threshold-based action signal generator producing BUY, SELL, or HOLD
- Add plain-text structured logging of timestamp, price, signal, and derived values per bar
- Add a dry-run execution guard that prevents any order placement

## Capabilities

### New Capabilities

- `credential-loading`: Load and validate Alpaca API credentials from environment variables
- `bar-fetching`: Fetch and normalize recent BTC/USD OHLCV bars from Alpaca, excluding incomplete bar
- `feature-computation`: Compute rolling statistics (mean, std, z-score, returns) on close prices
- `signal-generation`: Generate BUY/SELL/HOLD action signals from derived features using fixed thresholds
- `run-logging`: Emit plain-text log lines containing timestamp, price, signal, and derived values
- `dry-run-guard`: Enforce dry-run mode so no orders are placed during signal generation runs

### Modified Capabilities

## Impact

- **New dependencies**: `alpaca-py`, `pandas`, `python-dotenv` (or `os.environ` only)
- **No existing code affected**: greenfield phase
- **No order placement**: all Alpaca trade endpoints are out of scope
- **No ML, multi-symbol, portfolio, or deployment concerns** in this phase
