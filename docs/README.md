# Early Breakout Scanner 

A modular stock scanner focused on detecting early breakout signals before stocks make major moves. This scanner identifies stocks showing signs of volume_anomalies, momentum divergences, relative strength, and compression.


# Core Detection Signals 

1. **Volume Detection**
   - Detects pullbacks on light volume (no selling pressure)
   - Checks if price holds above 21 EMA
   - Scores 0-10 based on volume patterns

2. **Momentum Divergences**
   - RSI rising while price consolidates (hidden strength)
   - MACD histogram turning positive
   - OBV trending upward (institutional buying)
   - Scores 0-10 based on divergence strength

3. **Relative Strength vs SPY**
   - Stock outperforming market during consolidation
   - RS ratio increasing over 5 days
   - Scores 0-10 based on outperformance

4. **Compression**
   - ATR calculations 
   - Price from recent highs 
   - Is stock compressing..coiling
