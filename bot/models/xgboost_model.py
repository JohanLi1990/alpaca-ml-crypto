"""XGBoost classifier training, persistence, and SHAP feature importance.

Phase 4 replaces logistic regression with a gradient-boosted tree classifier.
XGBoost can capture non-linear interactions between regime features (e.g.
"high-vol AND strong-trend → continuation") that logistic regression cannot.

SHAP (SHapley Additive exPlanations) values explain each model prediction by
attributing the output to each feature.  Logging mean absolute SHAP values per
fold lets us track which features drive performance across OOS windows.
"""
from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from xgboost import XGBClassifier


def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
    """Train an XGBoost classifier with time-series-safe hyperparameter search.

    Uses ``GridSearchCV`` with ``TimeSeriesSplit(n_splits=3)`` to prevent
    lookahead bias during cross-validation.  Searches over depth, learning
    rate, and subsample fraction; fixes ``n_estimators=200``.

    Args:
        X_train: Feature DataFrame (rows = bars, columns = feature names).
        y_train: Binary label Series (0 = flat, 1 = long), same index as X_train.

    Returns:
        The best-fitted ``XGBClassifier`` (by mean CV log-loss).
    """
    param_grid = {
        "max_depth":     [2, 3, 4],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample":     [0.7, 0.9],
    }

    # Use fewer estimators during the CV search to keep grid search fast,
    # then refit the best params with the full 200 estimators.
    search_model = XGBClassifier(
        n_estimators=50,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
        verbosity=0,
    )

    cv = TimeSeriesSplit(n_splits=3)

    search = GridSearchCV(
        estimator=search_model,
        param_grid=param_grid,
        scoring="neg_log_loss",
        cv=cv,
        refit=False,  # we'll refit manually with n_estimators=200
        n_jobs=-1,
    )
    search.fit(X_train, y_train)

    # Refit with full depth using the best hyperparameters found
    best_params = search.best_params_
    final_model = XGBClassifier(
        n_estimators=200,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
        verbosity=0,
        **best_params,
    )
    final_model.fit(X_train, y_train)
    return final_model


def save_xgboost(model: XGBClassifier, path: str) -> None:
    """Save an XGBoost model to disk using XGBoost's native JSON serialisation.

    Args:
        model: Fitted ``XGBClassifier`` to save.
        path:  Destination file path (should end in ``.json``).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    model.save_model(path)


def load_xgboost(path: str) -> XGBClassifier:
    """Load an XGBoost model from a ``.json`` artifact.

    Args:
        path: Path to a model file previously saved with ``save_xgboost``.

    Returns:
        Ready-to-predict ``XGBClassifier``.
    """
    model = XGBClassifier()
    model.load_model(path)
    return model


def compute_shap_importance(
    model: XGBClassifier,
    X_test: pd.DataFrame,
) -> dict[str, float]:
    """Compute mean absolute SHAP values for the test set.

    Uses ``shap.TreeExplainer`` (fast, exact for tree-based models) to compute
    SHAP values for every test bar, then averages the absolute values per
    feature.  Higher values indicate features that had a larger average impact
    on model predictions.

    Args:
        model:  Fitted ``XGBClassifier``.
        X_test: Feature DataFrame for the test set (same columns as training).

    Returns:
        Dict mapping ``feature_name → mean_abs_shap_value``, sorted descending.
    """
    explainer = shap.TreeExplainer(model)
    # shap_values has shape (n_samples, n_features) for binary classification
    shap_values: np.ndarray = explainer.shap_values(X_test)

    # Handle cases where TreeExplainer returns a list (one array per class)
    if isinstance(shap_values, list):
        # Use class-1 (long) SHAP values
        shap_values = shap_values[1]

    mean_abs = np.abs(shap_values).mean(axis=0)
    importance: dict[str, float] = {
        col: float(val) for col, val in zip(X_test.columns, mean_abs)
    }
    # Sort descending by importance
    return dict(sorted(importance.items(), key=lambda kv: kv[1], reverse=True))
