# pre-breakout-analyzer
Scans for stocks about to breakout 

# Early Breakout Scanner 🚀

A modular stock scanner focused on detecting **early breakout signals** before stocks make major moves. This scanner identifies stocks showing signs of institutional accumulation, momentum divergences, and relative strength.

---

## 📋 Features

### Core Detection Signals (Steps 5-7)

1. **Step 5: Volume Dry-Up During Pullback**
   - Detects pullbacks on light volume (no selling pressure)
   - Checks if price holds above 21 EMA
   - Scores 0-10 based on volume patterns

2. **Step 6: Momentum Divergences**
   - RSI rising while price consolidates (hidden strength)
   - MACD histogram turning positive
   - OBV trending upward (institutional buying)
   - Scores 0-10 based on divergence strength

3. **Step 7: Relative Strength vs SPY**
   - Stock outperforming market during consolidation
   - RS ratio increasing over 5 days
   - Scores 0-10 based on outperformance

### Alert System

- **Triggers**: Stocks meeting **2 out of 3 signals**
- **Discord Notifications**: Real-time alerts with details
- **CSV Export**: Daily ranked results for analysis

---

## 🏗️ Project Structure

```
early-breakout-scanner/
│
├── config.py                      # Configuration settings
├── data_fetcher.py               # Yahoo Finance data retrieval
├── utils.py                      # Technical indicator calculations
├── scanner.py                    # Main scanner orchestrator
├── discord_alert.py              # Discord webhook notifications
│
├── signals/
│   ├── step5_volume_dryup.py     # Volume dry-up detection
│   ├── step6_divergences.py      # Momentum divergence detection
│   └── step7_relative_strength.py # Relative strength analysis
│
├── ticker_list.txt               # Your stock watchlist (one per line)
├── requirements.txt              # Python dependencies
│
└── results/
    └── scan_results_YYYY-MM-DD.csv  # Daily scan outputs
```

---

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Discord Webhook (Optional)

1. Create a Discord webhook in your server
2. Open `config.py`
3. Replace `YOUR_DISCORD_WEBHOOK_URL_HERE` with your webhook URL

### 3. Add Your Ticker List

Replace `ticker_list.txt` with your validated ticker list:

```
AAPL
TSLA
NVDA
...
```

One ticker per line, no commas.

---

## ▶️ Usage

### Run the Scanner

```bash
python scanner.py
```

### What Happens

1. **Loads** your ticker list
2. **Fetches** SPY data for relative strength
3. **Scans** each stock through all 3 signals
4. **Saves** results to CSV (`results/scan_results_YYYY-MM-DD.csv`)
5. **Sends** Discord alerts for stocks meeting criteria (2+ signals)
6. **Displays** top 10 ranked stocks in terminal

---

## 📊 Output Files

### CSV Columns

| Column | Description |
|--------|-------------|
| `ticker` | Stock symbol |
| `signals_met` | Number of signals triggered (0-3) |
| `total_score` | Combined score from all signals (0-30) |
| `step5_signal` | Volume dry-up detected (True/False) |
| `step6_signal` | Divergences detected (True/False) |
| `step7_signal` | Relative strength detected (True/False) |
| `current_price` | Latest closing price |
| `volume` | Latest volume |

Plus detailed metrics for each signal step.

---

## ⚙️ Configuration

Edit `config.py` to customize:

### Alert Threshold
```python
ALERT_THRESHOLD = 2  # Alert when 2 out of 3 signals met
```

### Volume Dry-Up Settings
```python
STEP5_LOOKBACK_PERIOD = 20  # Days for volume average
STEP5_RED_DAY_VOLUME_RATIO = 0.7  # Red day volume threshold
STEP5_EMA_PERIOD = 21  # EMA support level
```

### Divergence Settings
```python
STEP6_RSI_PERIOD = 14
STEP6_RSI_LOOKBACK = 5  # Days to check RSI trend
STEP6_OBV_LOOKBACK = 5  # Days to check OBV slope
```

### Relative Strength Settings
```python
STEP7_RS_LOOKBACK = 5  # Days for RS calculation
STEP7_SPY_SYMBOL = "SPY"  # Benchmark
```

---

## 🔄 Upgrading to Polygon.io

When ready to upgrade from Yahoo Finance to Polygon:

1. Sign up at [polygon.io](https://polygon.io)
2. Get your API key
3. Replace `data_fetcher.py` with Polygon implementation
4. Keep all signal files unchanged (they're data-source agnostic)

---

## 📈 Example Workflow

### Daily Routine

1. **Morning**: Run scanner after market close
   ```bash
   python scanner.py
   ```

2. **Review**: Check Discord for alerts

3. **Analyze**: Open CSV for detailed breakdown

4. **Research**: Investigate top-scored stocks on your platform

5. **Track**: Monitor alerted stocks for entry points

---

## 🎯 Scoring System

Each signal scores **0-10 points**:

- **Total Score Range**: 0-30 points
- **Alert Threshold**: Stock must score ≥5 in at least 2 signals
- **Ranking**: Stocks ranked by total score (higher = stronger setup)

### Interpretation

| Score Range | Meaning |
|-------------|---------|
| 20-30 | Strong early breakout setup |
| 15-19 | Moderate setup, watch closely |
| 10-14 | Weak setup, early accumulation phase |
| 0-9 | Insufficient signals |

---

## 🐛 Troubleshooting

### No Data for Ticker
- Verify ticker symbol is correct
- Check if stock has sufficient trading history (60+ days)

### Discord Alerts Not Sending
- Verify webhook URL in `config.py`
- Test webhook manually in Discord settings

### Scan Too Slow
- Reduce ticker list size
- Consider upgrading to Polygon.io (much faster)

---

## 🔮 Future Enhancements

Potential additions (discussed but not implemented yet):

- Chaikin Money Flow (CMF)
- Bollinger Band Squeeze
- Pocket Pivot detection
- Float rotation analysis
- Anchored VWAP

---

## 📝 Notes

- **Data Source**: Currently uses Yahoo Finance (free but slower)
- **Scan Frequency**: Designed for daily after-market scans
- **Modular Design**: Each signal is independent for easy testing/modification
- **Upgrade Path**: Built to easily swap Yahoo Finance → Polygon.io

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Modify thresholds in `config.py`
- Add new signals in `signals/` folder
- Improve scoring logic
- Test with different ticker universes

---

## ⚠️ Disclaimer

This scanner is for **educational and research purposes only**. Not financial advice. Always do your own research before trading.

---

**Built with:** Python, yfinance, pandas, numpy
**License:** Personal Use
**Version:** 1.0