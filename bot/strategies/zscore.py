import numpy as np
import pandas as pd

from bot.config import ZSCORE_LOWER, ZSCORE_UPPER


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Assign a BUY / SELL / HOLD action signal to each bar.

    Rules (strict inequalities — boundary values map to HOLD):
        zscore >  ZSCORE_UPPER  -> BUY
        zscore <  ZSCORE_LOWER  -> SELL
        otherwise               -> HOLD

    Returns:
        DataFrame with an additional ``signal`` column (no NaN values).
    """
    df = df.copy()

    df["signal"] = np.select(
        [df["zscore"] > ZSCORE_UPPER, df["zscore"] < ZSCORE_LOWER],
        ["BUY", "SELL"],
        default="HOLD",
    )

    assert df["signal"].isna().sum() == 0, "Unexpected NaN values in signal column"

    return df
