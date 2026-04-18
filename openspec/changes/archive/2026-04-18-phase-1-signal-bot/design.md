## Context

Greenfield implementation. No existing application code. The Alpaca Python client (`alpaca-py`) provides the data API. Phase 1 is intentionally scoped to a deterministic rule-based signal pipeline as the testable foundation for future ML phases. Key constraint: output must be fully reproducible given the same input dataset.

## Goals / Non-Goals

**Goals:**
- Establish a working end-to-end pipeline: credentials → data → features → signal → log
- Ensure reproducible output for the same input dataset
- Enforce a hard dry-run execution gate with no order side effects
- Keep the architecture readable with purpose-grouped modules and minimal abstraction

**Non-Goals:**
- Machine learning, model training, or inference
- Multi-symbol or multi-timeframe support
- Portfolio optimization or position sizing
- Live order placement (deferred to future phase)
- Deployment, containerization, or scheduling
- Advanced risk engine or stop-loss logic

## Decisions

### D1: Action signals (BUY/SELL/HOLD) over state signals (LONG/SHORT/FLAT)

**Chosen**: Action semantics — BUY, SELL, HOLD.

**Rationale**: Action signals represent intent at each bar boundary, making them directly interpretable in logs and future broker integration. State signals (LONG/SHORT/FLAT) describe portfolio position and require tracking prior state to be meaningful. For a stateless phase 1 pipeline this creates unnecessary complexity.

**Alternative considered**: LONG/SHORT/FLAT — rejected because it implies persistent position tracking which is out of scope.

---

### D2: Exclude the last incomplete bar

**Chosen**: Always drop the most recent bar before feature computation.

**Rationale**: The last bar in any real-time fetch is typically still forming. Including it causes non-deterministic results for the same nominal time window across multiple runs. Excluding it makes the dataset stable and reproducible given the same fetch timestamp.

**Alternative considered**: Include all bars — rejected because it breaks the reproducibility acceptance criterion.

---

### D3: Z-score threshold rule for signal generation

**Chosen**: Compute a rolling z-score on close price and apply symmetric upper/lower thresholds to classify each bar.

**Rationale**: Simple, interpretable, deterministic, and parameter-transparent. Threshold values are fixed in config so the same dataset always produces the same signals.

**Alternatives considered**:
- Raw price crossover — too sensitive to absolute price levels across time.
- Percent change threshold — reasonable, but z-score provides automatic normalization.

---

### D4: Plain-text structured log lines

**Chosen**: Each processed bar emits one human-readable log line with a fixed field order.

**Rationale**: Readable in terminal, trivially parseable with `grep` or `awk`, no dependencies. Sufficient for phase 1 where the audience is the developer, not a monitoring system.

**Alternative considered**: JSON structured logging — deferred to a later phase.

---

### D5: Warm-up rows with NaN features are silently dropped

**Chosen**: Rows where rolling statistics are undefined (the initial warm-up window) are excluded from signal generation and logging.

**Rationale**: NaN-based signals are undefined. Dropping these rows ensures the signal loop always operates on fully-defined feature vectors. The fetch size must be large enough that at least 100 fully-computed rows remain after warm-up.

---

### D6: Credentials loaded strictly from environment variables

**Chosen**: `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` loaded via `os.environ` or `.env` file via `python-dotenv`.

**Rationale**: Keeps credentials out of source code and config files. Fails fast with a clear error message if either variable is missing.

---

### D7: Organize code by purpose-aligned subpackages

**Chosen**: Group modules into subpackages by responsibility:
- `bot/data` for data access
- `bot/features` for feature engineering
- `bot/strategies` for signal/strategy logic
- `bot/utils` for credentials and logging helpers

**Rationale**: Improves maintainability as strategy and feature count grows while keeping the Phase 1 flow simple and deterministic.

**Alternative considered**: Keep all modules flat in `bot/` — rejected because it scales poorly for upcoming multi-strategy and ML phases.

## Risks / Trade-offs

- **Fewer than 100 usable bars after warm-up** → Mitigation: validate bar count after dropping incomplete bar and warm-up rows, raise explicit error if count < 100.
- **Alpaca API response ordering** → Mitigation: always sort ascending by timestamp after fetch, do not rely on API sort order.
- **Timezone inconsistency** → Mitigation: normalize all timestamps to UTC immediately after fetch.
- **Threshold boundary equality** → Mitigation: define exact rule in spec (`>` for BUY, `<` for SELL, else HOLD) so boundary-touching values always resolve to HOLD.
- **Float formatting drift in logs** → Mitigation: fix decimal precision for logged fields in the run-logging spec.
