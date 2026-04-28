"""
Configuration file for Early Breakout Scanner
"""

# ===== FILE PATHS =====
TICKER_LIST_PATH = "test_tickers.txt"

RESULTS_FOLDER = "results"

# ===== VOLUME DRY-UP THRESHOLDS =====
VOLUME_LOOKBACK_PERIOD = 20  # Days to calculate average volume
VOLUME_EMA_PERIOD = 21  # EMA period for pullback support

# ===== MOMENTUM DIVERGENCE THRESHOLDS =====
DIVERGENCE_RSI_PERIOD = 14
DIVERGENCE_RSI_LOOKBACK = 10  
DIVERGENCE_MACD_FAST = 12
DIVERGENCE_MACD_SLOW = 26
DIVERGENCE_MACD_SIGNAL = 9

# ===== RELATIVE STRENGTH THRESHOLDS =====
RS_LOOKBACK_SHORT = 10
RS_LOOKBACK_LONG = 60 
SPY_SYMBOL = 'SPY'

# ===== DATA FETCH =====
DATA_LOOKBACK_DAYS = 250  # Total days of historical data to fetch