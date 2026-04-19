import os

import joblib
import pandas as pd

from bot.config import LOGREG_CONFIDENCE_THRESHOLD

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "logreg.pkl")
_MODEL_PATH = os.path.normpath(_MODEL_PATH)

_FEATURE_COLS = [
    "rolling_mean",
    "rolling_std",
    "zscore",
    "return",
    "return_lag1",
    "return_lag2",
    "return_lag3",
    "momentum_12h",
    "volume_zscore_20",
]


def _load_model():
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(
            f"LogReg model not found at {_MODEL_PATH}. "
            "Run notebooks/phase2_backtest.ipynb to train and save the model first."
        )
    return joblib.load(_MODEL_PATH)


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Generate long/flat signals using the trained logistic regression model.

    Loads the persisted model from bot/models/logreg.pkl. Computes P(label=1)
    for each bar and assigns signal 1 (long) when the probability exceeds
    LOGREG_CONFIDENCE_THRESHOLD, else 0 (flat).

    Returns:
        DataFrame with an additional ``signal`` column (int: 0 or 1, no NaN).

    Raises:
        FileNotFoundError: if bot/models/logreg.pkl does not exist.
    """
    model = _load_model()

    feature_cols = [c for c in _FEATURE_COLS if c in df.columns]
    X = df[feature_cols]

    prob_long = model.predict_proba(X)[:, 1]
    df = df.copy()
    df["signal"] = (prob_long > LOGREG_CONFIDENCE_THRESHOLD).astype(int)

    assert df["signal"].isna().sum() == 0, "Unexpected NaN values in signal column"

    return df
