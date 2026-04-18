SYMBOL = "BTC/USD"
BAR_LIMIT = 300          # bars to request; enough to survive warm-up + 100 usable rows
ROLLING_WINDOW = 20      # bars used for rolling mean / std
ZSCORE_UPPER = 1.0       # zscore > ZSCORE_UPPER  -> BUY
ZSCORE_LOWER = -1.0      # zscore < ZSCORE_LOWER  -> SELL
MIN_BARS_AFTER_FETCH = 150
MIN_BARS_AFTER_FEATURES = 100
