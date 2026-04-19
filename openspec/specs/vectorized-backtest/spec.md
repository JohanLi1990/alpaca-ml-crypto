## ADDED Requirements

### Requirement: Accept an optional signal policy function in run_backtest
`run_backtest` SHALL accept an optional `policy_fn` callable parameter. When provided, `policy_fn` is called on the `signal` column before it is lagged and applied to bar returns. When not provided, the raw signal column is used unchanged (preserving Phase 2 behavior exactly).

#### Scenario: Policy function applied when provided
- **WHEN** `run_backtest(df, policy_fn=my_policy)` is called
- **THEN** `policy_fn(df["signal"])` is called first, and its output replaces `df["signal"]` for the remainder of the backtest computation

#### Scenario: Phase 2 behavior preserved when policy_fn is None
- **WHEN** `run_backtest(df)` is called without `policy_fn`
- **THEN** the backtest behaves identically to Phase 2 (no signal transformation applied)
