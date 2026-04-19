## ADDED Requirements

### Requirement: Compute Brier score for model probability quality
`compute_calibration_metrics` SHALL compute the Brier score as `mean((prob_t - y_t)^2)` over all labeled bars in the evaluation set. The Brier score measures the accuracy of probability forecasts independently of any trading threshold.

#### Scenario: Brier score computed correctly
- **WHEN** `compute_calibration_metrics(y_true, prob_series)` is called
- **THEN** `brier_score` equals `mean((prob_series - y_true)^2)` and is a float in `[0.0, 1.0]`

#### Scenario: Perfect calibration yields Brier score of 0
- **WHEN** `prob_series` equals `y_true` exactly (all 0.0 or 1.0, perfectly correct)
- **THEN** `brier_score` equals `0.0`

#### Scenario: Random guessing at 0.5 yields Brier score of 0.25
- **WHEN** `prob_series` is a constant `0.5` for a balanced binary target
- **THEN** `brier_score` equals approximately `0.25`

### Requirement: Compute calibration bins for reliability diagram
`compute_calibration_metrics` SHALL compute calibration statistics using 10 equal-width probability bins. For each bin, record the mean predicted probability and the observed fraction of positive labels. These data SHALL be returned as a dict keyed by bin center.

#### Scenario: Calibration bins computed
- **WHEN** `compute_calibration_metrics` returns
- **THEN** `calibration_bins` is a dict with up to 10 keys (bin centers) and each value is a dict with `mean_predicted_prob` and `fraction_positive`

#### Scenario: Empty bins excluded
- **WHEN** a probability bin contains no samples
- **THEN** that bin center is omitted from `calibration_bins` rather than returning NaN

### Requirement: Return calibration metrics as a structured dict
`compute_calibration_metrics` SHALL return a single dict with at minimum the keys `brier_score` and `calibration_bins`.

#### Scenario: Return dict structure
- **WHEN** `compute_calibration_metrics(y_true, prob_series)` returns
- **THEN** the returned dict contains the keys `brier_score` (float) and `calibration_bins` (dict)

### Requirement: Accept y_true as a boolean-compatible series and prob_series as a float series
`compute_calibration_metrics` SHALL accept a binary integer or boolean `y_true` Series and a float probability Series (values in `[0.0, 1.0]`). Both MUST have the same index; a `ValueError` SHALL be raised if they do not.

#### Scenario: Mismatched indices raise ValueError
- **WHEN** `y_true` and `prob_series` have different indices
- **THEN** a `ValueError` is raised with a descriptive message
