## ADDED Requirements

### Requirement: Accept a dict of aligned symbol DataFrames as input
`compute_cross_asset_features` SHALL accept a `dict[str, pd.DataFrame]` mapping symbol names to their feature DataFrames (e.g., `{"BTC/USD": df_btc, "ETH/USD": df_eth}`). Each DataFrame MUST share a common timestamp index. The function SHALL align them by index intersection before computing relative features.

#### Scenario: Multi-symbol input accepted
- **WHEN** `compute_cross_asset_features({"BTC/USD": df_btc, "ETH/USD": df_eth, "SOL/USD": df_sol})` is called
- **THEN** the function aligns all DataFrames to the intersection of their timestamp indices before computation

#### Scenario: Misaligned timestamps handled by intersection
- **WHEN** two symbol DataFrames have different timestamp sets
- **THEN** only rows present in all DataFrames are included in the output

### Requirement: Compute rolling return spread between reference and companion symbols
For each companion symbol, the system SHALL compute `{ref}_excess_return_vs_{companion}` as the rolling 12-bar sum of `(ref_return - companion_return)` at each bar `t`. The reference symbol defaults to `BTC/USD`.

#### Scenario: BTC excess return vs ETH computed
- **WHEN** BTC/USD and ETH/USD DataFrames are provided
- **THEN** column `btc_excess_return_vs_eth` is present with values equal to the 12-bar rolling sum of `(btc_return_t - eth_return_t)`

#### Scenario: BTC excess return vs SOL computed
- **WHEN** BTC/USD and SOL/USD DataFrames are provided
- **THEN** column `btc_excess_return_vs_sol` is present with values equal to the 12-bar rolling sum of `(btc_return_t - sol_return_t)`

### Requirement: No future leakage in cross-asset features
All cross-asset features SHALL be computed using only bar returns available at or before bar `t`. No cross-asset feature may reference any return from bar `t+1` or later.

#### Scenario: Rolling window closes at bar t
- **WHEN** any cross-asset feature is computed at bar `t`
- **THEN** the 12-bar window uses bars `t-11` through `t` only

### Requirement: Return the reference symbol DataFrame with cross-asset features appended
`compute_cross_asset_features` SHALL return the reference symbol's DataFrame with cross-asset feature columns added. The returned DataFrame SHALL cover only the aligned timestamp intersection.

#### Scenario: Cross-asset columns appended to reference DataFrame
- **WHEN** `compute_cross_asset_features` returns
- **THEN** the reference symbol's DataFrame contains all original columns plus one `excess_return` column per companion symbol

#### Scenario: No NaN in cross-asset feature columns after warm-up drop
- **WHEN** the returned DataFrame is examined
- **THEN** cross-asset feature columns contain no NaN values beyond the first 11 warm-up rows (which SHALL be dropped)

### Requirement: Graceful handling of missing companion symbol
If a companion symbol is absent from the input dict, the system SHALL skip that companion's feature column and emit a warning rather than raising an exception.

#### Scenario: Missing companion symbol skipped
- **WHEN** `compute_cross_asset_features` is called with only BTC/USD and ETH/USD (no SOL/USD)
- **THEN** `btc_excess_return_vs_eth` is computed, `btc_excess_return_vs_sol` is omitted, and a `UserWarning` is emitted
