## ADDED Requirements

### Requirement: Train logistic regression with time-ordered split
The system SHALL split the labeled dataset into training (first 80%) and test (last 20%) sets in temporal order, with no shuffling, and train a logistic regression classifier on the training set only.

#### Scenario: Temporal split enforced
- **WHEN** the dataset is split for training
- **THEN** all training rows precede all test rows in time, with no shuffling applied

#### Scenario: Model trained on training split only
- **WHEN** the logistic regression is fit
- **THEN** the model's `fit()` call uses only training split features and labels

### Requirement: Regularization grid search with TimeSeriesSplit
The system SHALL select the best regularization parameter `C` from `[0.01, 0.1, 1.0, 10.0]` using `GridSearchCV` with `TimeSeriesSplit(n_splits=5)` and F1 scoring.

#### Scenario: Grid search runs over C values
- **WHEN** training is initiated
- **THEN** all four values of C are evaluated and the best C by mean F1 is selected

#### Scenario: TimeSeriesSplit prevents leakage in CV
- **WHEN** cross-validation folds are created during grid search
- **THEN** each validation fold contains only bars that come after all bars in the corresponding training fold

### Requirement: Balanced class weights
The system SHALL configure `class_weight='balanced'` on the logistic regression estimator to compensate for any residual class imbalance after quantile filtering.

#### Scenario: Balanced weights applied
- **WHEN** the logistic regression is instantiated
- **THEN** `class_weight='balanced'` is set and the estimator accounts for class frequency differences

### Requirement: Persist trained model to disk
The system SHALL save the best-fit model to `bot/models/logreg.pkl` using `joblib.dump` at the end of the training notebook.

#### Scenario: Model file created
- **WHEN** training completes successfully
- **THEN** `bot/models/logreg.pkl` exists and is loadable by `joblib.load`

### Requirement: Load persisted model for live signal generation
The `logreg` strategy module SHALL load the persisted model from `bot/models/logreg.pkl` at initialization. If the file does not exist, it SHALL raise a `FileNotFoundError` with a message instructing the user to run the training notebook.

#### Scenario: Model loaded successfully
- **WHEN** `bot/models/logreg.pkl` exists
- **THEN** the strategy initializes without error and the model is ready for inference

#### Scenario: Model file missing
- **WHEN** `bot/models/logreg.pkl` does not exist
- **THEN** a `FileNotFoundError` is raised with a message referencing the notebook that must be run first

### Requirement: Generate prediction-based signals
The logistic regression strategy SHALL output a long (`1`) signal when `P(label=1)` exceeds a configurable confidence threshold (default: 0.6), and a flat (`0`) signal otherwise.

#### Scenario: High-confidence long signal
- **WHEN** the model predicts `P(label=1) > LOGREG_CONFIDENCE_THRESHOLD`
- **THEN** the signal for that bar is `1` (long)

#### Scenario: Below-threshold flat signal
- **WHEN** the model predicts `P(label=1) <= LOGREG_CONFIDENCE_THRESHOLD`
- **THEN** the signal for that bar is `0` (flat)
