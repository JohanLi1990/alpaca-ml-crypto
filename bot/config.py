SYMBOL = "BTC/USD"
BAR_LIMIT = 300          # bars to request; enough to survive warm-up + 100 usable rows
ROLLING_WINDOW = 20      # bars used for rolling mean / std
ZSCORE_UPPER = 1.0       # zscore > ZSCORE_UPPER  -> BUY
ZSCORE_LOWER = -1.0      # zscore < ZSCORE_LOWER  -> SELL
MIN_BARS_AFTER_FETCH = 150
MIN_BARS_AFTER_FEATURES = 100

# ── Phase 2: ML / backtesting ────────────────────────────────────────────────
HISTORY_MONTHS = 6                  # months of historical data to fetch for training
MIN_BARS_HISTORY = 500              # minimum bars required for ML training
TRANSACTION_FEE = 0.002             # 0.20% per trade (conservative Alpaca crypto estimate)
LOGREG_CONFIDENCE_THRESHOLD = 0.54  # P(label=1) must exceed this to generate a long signal

# ── Phase 3: Robustness ──────────────────────────────────────────────────────
ATR_WINDOW = 14                    # bars for Average True Range (≈ 14 hours on hourly data)
REGIME_VOL_WINDOW = 252            # bars for volatility percentile rolling window (≈ 10.5 days)
TREND_SLOPE_WINDOW = 24            # bars for OLS trend slope window (≈ 1 day on hourly data)
WALKFORWARD_TRAIN_BARS = 1800      # training bars per walk-forward fold (≈ 75 days)
WALKFORWARD_VAL_BARS = 600         # validation bars per fold (reserved for model selection)
WALKFORWARD_TEST_BARS = 600        # OOS test bars per fold — the bars we evaluate on
WALKFORWARD_N_FOLDS = 4            # number of walk-forward folds to attempt
ABSTAIN_LO = 0.45                  # model probability below this → bearish → no trade
ABSTAIN_HI = 0.55                  # model probability above this → confident long → trade
MIN_HOLD_BARS = 1                  # minimum bars to hold a long position (1 = no enforced hold)

# ── Phase 4: Daily XGBoost ───────────────────────────────────────────────────
DAILY_LOOKBACK_DAYS = 730          # calendar days of daily bars to fetch (~2 years)
DAILY_ATR_WINDOW = 14              # bars for ATR on daily data (14 days ≈ 2 calendar weeks)
DAILY_FORWARD_BARS = 5             # forward return horizon for daily labels (5 trading days)
DAILY_REGIME_VOL_WINDOW = 60       # bars for vol percentile on daily data (~3 months)
DAILY_TREND_SLOPE_WINDOW = 10      # bars for OLS trend slope on daily data (~2 weeks)
DAILY_WALKFORWARD_TRAIN_BARS = 350 # training bars per walk-forward fold (~17 months)
DAILY_WALKFORWARD_VAL_BARS = 120   # validation bars per fold (~6 months, buffered for feature warm-up)
DAILY_WALKFORWARD_TEST_BARS = 120  # OOS test bars per fold (~6 months, buffered for feature warm-up)
DAILY_WALKFORWARD_N_FOLDS = 2      # number of walk-forward folds to attempt (reduced to fit 730 bars)
