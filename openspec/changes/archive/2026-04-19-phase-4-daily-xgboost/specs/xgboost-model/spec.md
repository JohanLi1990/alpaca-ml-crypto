## ADDED Requirements

### Requirement: Train an XGBoost classifier on labeled feature data
The system SHALL expose a `train_xgboost(X_train, y_train)` function in `bot/models/xgboost_model.py` that trains an `xgboost.XGBClassifier` using time-series-safe hyperparameter search and returns the best fitted model.

#### Scenario: Model trained and returned
- **WHEN** `train_xgboost(X_train, y_train)` is called with a non-empty labeled DataFrame
- **THEN** a fitted `XGBClassifier` object is returned with `predict_proba` available

#### Scenario: Hyperparameter search via TimeSeriesSplit
- **WHEN** training is invoked
- **THEN** the system runs `GridSearchCV` with `TimeSeriesSplit(n_splits=3)` over the parameter grid: `max_depth` ∈ [2, 3, 4], `learning_rate` ∈ [0.05, 0.1, 0.2], `subsample` ∈ [0.7, 0.9], `n_estimators=200`
- **AND** the best estimator by mean cross-validation log-loss is returned

### Requirement: Persist and load XGBoost model artifact
The system SHALL save the trained XGBoost model to `bot/models/<symbol_slug>_xgboost.json` using XGBoost's native JSON serialisation. The system SHALL provide a `load_xgboost(path)` function that restores the model from disk.

#### Scenario: Model saved as JSON artifact
- **WHEN** a model is trained and saved
- **THEN** a `.json` file exists at the expected path and can be loaded back with identical `predict_proba` output

### Requirement: Log per-fold SHAP feature importance
The system SHALL compute mean absolute SHAP values for the test set of each walk-forward fold using `shap.TreeExplainer` and log a ranked feature importance dict alongside the fold metrics.

#### Scenario: SHAP values computed for every completed fold
- **WHEN** a walk-forward fold completes successfully
- **THEN** the fold result dict includes a `shap_importance` key mapping feature name → mean absolute SHAP value, sorted descending

#### Scenario: SHAP computation does not raise for any supported feature set
- **WHEN** SHAP values are requested on any feature DataFrame produced by `compute_features`
- **THEN** no exception is raised and all feature columns have a corresponding SHAP entry
