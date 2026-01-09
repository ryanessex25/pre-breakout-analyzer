# Early Breakout Scanner 

A modular stock scanner focused on detecting **early breakout signals** before stocks make major moves. This scanner identifies stocks showing signs of institutional accumulation, momentum divergences, and relative strength...

---
## Features

### Core Detection Signals 

1. **Step 1: Volume Dry-Up During Pullback**
   - Detects pullbacks on light volume (no selling pressure)
   - Checks if price holds above 21 EMA
   - Scores 0-10 based on volume patterns

2. **Step 2: Momentum Divergences**
   - RSI rising while price consolidates (hidden strength)
   - MACD histogram turning positive
   - OBV trending upward (institutional buying)
   - Scores 0-10 based on divergence strength

3. **Step 3: Relative Strength vs SPY**
   - Stock outperforming market during consolidation
   - RS ratio increasing over 5 days
   - Scores 0-10 based on outperformance

### Alert System

- **Triggers**: Stocks meeting **2 out of 3 signals**
- **Discord Notifications**: Real-time alerts with details
- **CSV Export**: Daily ranked results for analysis

---

##  Configuration

Edit `config.py` to customize:

### Alert Threshold
ALERT_THRESHOLD = 2  # Alert when 2 out of 3 signals met


### Volume Dry-Up Settings
STEP1_LOOKBACK_PERIOD = 20  # Days for volume average
STEP1_RED_DAY_VOLUME_RATIO = 0.7  # Red day volume threshold
STEP1_EMA_PERIOD = 21  # EMA support level


### Divergence Settings
STEP2_RSI_PERIOD = 14
STEP2_RSI_LOOKBACK = 5  # Days to check RSI trend
STEP2_OBV_LOOKBACK = 5  # Days to check OBV slope


### Relative Strength Settings
STEP3_RS_LOOKBACK = 5  # Days for RS calculation
STEP3_SPY_SYMBOL = "SPY"  # Benchmark


---

##  Upgrading to Polygon.io

When ready to upgrade from Yahoo Finance to Polygon:

1. Sign up at [polygon.io](https://polygon.io)
2. Get your API key
3. Replace `data_fetcher.py` with Polygon implementation
4. Keep all signal files unchanged (they're data-source agnostic)


## Scoring System

Each signal scores **0-10 points**:

- **Total Score Range**: 0-30 points
- **Alert Threshold**: Stock must score ≥6-7 in at least 2 signals
- **Ranking**: Stocks ranked by total score (higher = stronger setup)

### Interpretation

| Score Range | Meaning |
|-------------|---------|
| 20-30 | Strong early breakout setup |
| 15-19 | Moderate setup, watch closely |
| 10-14 | Weak setup, early accumulation phase |
| 0-9 | Insufficient signals |

