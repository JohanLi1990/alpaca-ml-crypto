import pandas as pd


def log_bar(row: pd.Series, dry_run: bool) -> None:
    """Print one structured log line for a single processed bar."""
    print(
        f"{row['timestamp']} | "
        f"close={row['close']:.2f} | "
        f"signal={row['signal']:<4} | "
        f"zscore={row['zscore']:.4f} | "
        f"rolling_mean={row['rolling_mean']:.2f} | "
        f"rolling_std={row['rolling_std']:.2f}"
    )


def log_run(df: pd.DataFrame, dry_run: bool) -> None:
    """Emit one log line per bar in *df*."""
    for _, row in df.iterrows():
        log_bar(row, dry_run)
