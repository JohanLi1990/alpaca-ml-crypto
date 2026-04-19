import argparse
import os

from bot.config import BAR_LIMIT, ROLLING_WINDOW, SYMBOL, ZSCORE_LOWER, ZSCORE_UPPER
from bot.data.fetcher import fetch_bars
from bot.features.rolling import compute_features
from bot.utils.credentials import load_credentials
from bot.utils.logger import log_run


def _resolve_dry_run(args: argparse.Namespace) -> bool:
    """Determine dry-run mode from CLI flags → env var → default (True)."""
    if args.live:
        return False
    if args.dry_run:
        return True
    env_val = os.environ.get("DRY_RUN", "").strip().lower()
    if env_val in ("1", "true", "yes"):
        return True
    return True  # safe default


def _get_signal_generator(strategy: str):
    """Return the generate_signals function for the selected strategy."""
    if strategy == "zscore":
        from bot.strategies.zscore import generate_signals
        return generate_signals
    if strategy == "logreg":
        from bot.strategies.logreg import generate_signals
        return generate_signals
    raise ValueError(f"Unknown strategy: {strategy!r}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BTC/USD Signal Bot"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry-run mode (default — no orders placed)",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Enable live execution mode (order placement not yet implemented)",
    )
    parser.add_argument(
        "--strategy",
        choices=["zscore", "logreg"],
        default="zscore",
        help="Signal generation strategy (default: zscore)",
    )
    args = parser.parse_args()

    dry_run = _resolve_dry_run(args)
    mode_label = "[DRY-RUN]" if dry_run else "[LIVE]"

    # ── Startup banner ────────────────────────────────────────────────────────
    print("=" * 62)
    print(f"  {mode_label} Signal Bot")
    print(f"  Symbol        : {SYMBOL}")
    print(f"  Strategy      : {args.strategy}")
    print(f"  Bar limit     : {BAR_LIMIT}")
    print(f"  Rolling window: {ROLLING_WINDOW} bars")
    if args.strategy == "zscore":
        print(f"  Thresholds    : BUY > {ZSCORE_UPPER}, SELL < {ZSCORE_LOWER}")
    print("=" * 62)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    api_key, secret_key = load_credentials()

    print(f"Fetching {BAR_LIMIT} bars for {SYMBOL}...")
    df = fetch_bars(api_key, secret_key)
    print(f"  {len(df)} closed bars loaded.")

    extended = args.strategy == "logreg"
    df = compute_features(df, extended=extended)
    print(f"  {len(df)} bars after warm-up drop.")

    generate_signals = _get_signal_generator(args.strategy)
    df = generate_signals(df)

    print()
    log_run(df, dry_run)

    # ── Execution guard ───────────────────────────────────────────────────────
    if dry_run:
        print(
            f"\n{mode_label} Pipeline complete. "
            f"{len(df)} bars processed. No orders were placed."
        )
    else:
        # Order placement is out of scope for Phase 1/2 — guard is here for future phases.
        print(
            f"\n[LIVE] Pipeline complete. {len(df)} bars processed. "
            f"Order placement not yet implemented."
        )

