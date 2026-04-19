## ADDED Requirements

### Requirement: Implement an abstain band on model probabilities
`apply_signal_policy` SHALL map model probabilities to a discrete signal series. Bars where `prob < abstain_lo` SHALL be mapped to signal `0`; bars where `prob > abstain_hi` SHALL be mapped to signal `1`; bars where `abstain_lo <= prob <= abstain_hi` SHALL be mapped to signal `0` (no trade).

#### Scenario: High-confidence long signal generated
- **WHEN** a bar's model probability exceeds `abstain_hi`
- **THEN** the output signal for that bar is `1`

#### Scenario: Low-confidence bars abstain
- **WHEN** a bar's model probability falls within `[abstain_lo, abstain_hi]`
- **THEN** the output signal for that bar is `0` (abstain, not flat)

#### Scenario: Default abstain band is [0.45, 0.55]
- **WHEN** `apply_signal_policy` is called without specifying `abstain_lo` and `abstain_hi`
- **THEN** the default abstain band `[0.45, 0.55]` is used

### Requirement: Enforce a minimum hold period to reduce churn
`apply_signal_policy` SHALL enforce a minimum hold of `min_hold_bars` bars after entering a long position. Once a `1` signal is generated, the signal SHALL remain `1` for at least `min_hold_bars` bars regardless of the model probability, unless `abstain_lo` is provided and the bar's raw probability falls below `abstain_lo` before the hold expires (in which case the hold is released early).

#### Scenario: Minimum hold prevents premature exit
- **WHEN** a long position is entered and the next bar's probability drops into the abstain band before `min_hold_bars` bars have elapsed
- **THEN** the signal remains `1` for the remainder of the hold period

#### Scenario: Hold expires normally
- **WHEN** `min_hold_bars` bars have elapsed since entry and the current bar's probability is in the abstain band
- **THEN** the signal returns to `0`

#### Scenario: Default min hold is 1 bar (no enforced hold)
- **WHEN** `apply_signal_policy` is called without specifying `min_hold_bars`
- **THEN** the default `min_hold_bars=1` is used, effectively disabling the hold constraint

### Requirement: Return a discrete integer signal series aligned to the input index
`apply_signal_policy` SHALL return a `pd.Series` of integer type (0 or 1) with the same index as the input probability series. No NaN values are permitted in the output.

#### Scenario: Output signal index matches input
- **WHEN** `apply_signal_policy` returns
- **THEN** the output Series has the same index as the input probability Series

#### Scenario: No NaN in output signal
- **WHEN** the output signal series is examined
- **THEN** `signal.isna().sum() == 0`

### Requirement: Signal policy is applied after model inference, not inside the backtest engine
The signal policy SHALL be invoked as a discrete step between model probability output and `run_backtest`. `run_backtest` SHALL receive the post-policy signal column and remain unmodified.

#### Scenario: Policy applied before backtest input
- **WHEN** the Phase 3 pipeline runs
- **THEN** the sequence is: model → `apply_signal_policy(prob)` → `df["signal"] = policy_signal` → `run_backtest(df)`
