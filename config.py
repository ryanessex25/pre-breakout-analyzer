"""
Configuration file for Early Breakout Scanner
"""

# ===== DISCORD SETTINGS =====
DISCORD_WEBHOOK_URL = "https://canary.discord.com/api/webhooks/1451719046990135507/ewPUTmwI5HMTQtQEM2ZA-ZrnOe7bSMqorvKFI6iwwhz1g1XyYimjg0jkAukhnYff0zxY"  # Replace with your actual webhook URL

# ===== FILE PATHS =====
TICKER_LIST_PATH = "ticker_list.txt"
RESULTS_FOLDER = "results"

# ===== SCANNING SETTINGS =====
ALERT_THRESHOLD = 2  # Alert when stock meets 2 out of 3 signals

# ===== STEP 5: VOLUME DRY-UP THRESHOLDS =====
STEP5_LOOKBACK_PERIOD = 20  # Days to calculate average volume
STEP5_RED_DAY_VOLUME_RATIO = 0.7  # Red day volume < 0.7x 20-day avg
STEP5_EMA_PERIOD = 21  # EMA period for pullback support

# ===== STEP 6: MOMENTUM DIVERGENCE THRESHOLDS =====
STEP6_RSI_PERIOD = 14
STEP6_RSI_LOOKBACK = 5  # Days to check if RSI is rising
STEP6_OBV_LOOKBACK = 5  # Days to check if OBV slope is positive
STEP6_MACD_FAST = 12
STEP6_MACD_SLOW = 26
STEP6_MACD_SIGNAL = 9

# ===== STEP 7: RELATIVE STRENGTH THRESHOLDS =====
STEP7_RS_LOOKBACK = 5  # Days to calculate RS slope
STEP7_SPY_SYMBOL = "SPY"  # Benchmark for relative strength

# ===== DATA SETTINGS =====
DATA_LOOKBACK_DAYS = 60  # Total days of historical data to fetch