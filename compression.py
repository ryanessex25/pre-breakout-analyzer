from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Optional
from utility_calculations import atr


# Average True Range (ATR) 
# -------------------------
# Configuration for how we measure ATR compression.
@dataclass
class ATRCompressionConfig:
    atr_period: int = 14      # ATR lookback (14 = standard Wilder)
    lookback_bars: int = 10   # How far back we compare (10 days ago)
    factor: float = 0.70      # Compression threshold (today’s ATR < 0.7 × ATR_10_days_ago)



# Result structure — holds outputs and debug info.
@dataclass
class ATRCompressionResult:
    contracting: bool
    atr_today: float | None
    atr_lookback: float | None
    threshold_factor: float
    reason: str | None = None


# Core function
# If no config is passed in, it uses the defaults (ATR 14 / lookback 10 / factor 0.7).
def atr_compression(df: pd.DataFrame, cfg: ATRCompressionConfig | None = None) -> ATRCompressionResult:
    """Check if volatility (ATR) has contracted compared to n-bars ago."""
    if cfg is None:
        cfg = ATRCompressionConfig()


    # --- Input validation ---
    #Checks that you have enough candles to calculate ATR and the lookback comparison.
    #If you only have, say, 5 days of data, it returns early with a clear “insufficient_bars” reason.
    if df is None or len(df) < max(cfg.atr_period + cfg.lookback_bars + 2, 30):
        return ATRCompressionResult(
            contracting=False,
            atr_today=None,
            atr_lookback=None,
            threshold_factor=cfg.factor,
            reason="insufficient_bars",
        )

    # Compute ATR 
    atr_series = atr(df, period=cfg.atr_period, use_ema=True).dropna()

    if len(atr_series) <= cfg.lookback_bars:
        return ATRCompressionResult(False, None, None, cfg.factor, reason="insufficient_atr_window")

    # Extract today's and lookback ATR values
    atr_today = atr_series.iloc[-1].item()  # last ATR value (most recent candle)
    atr_lookback = atr_series.shift(cfg.lookback_bars).dropna().iloc[-1].item()  # ATR value 10 bars ago


    if not np.isfinite(atr_today) or not np.isfinite(atr_lookback):
        return ATRCompressionResult(False, None, None, cfg.factor, reason="non_finite_values")

    # Main condition: has ATR contracted?
    contracting = atr_today < (cfg.factor * atr_lookback)

    # Return structured result
    return ATRCompressionResult(
        contracting=bool(contracting),
        atr_today=atr_today,
        atr_lookback=atr_lookback,
        threshold_factor=cfg.factor,
        reason=None,
    )



# Price Near Recent High
# -------------------------
"""
Behavior:
Price consolidates tightly just under resistance — within 2–3% of the recent high.

Quantifiable Rule:
  • Close is within −3% (below) to 0% (equal) of the 10-day or 20-day high.
  • Optional check: both highs roughly equal (flat resistance).

If either 10-day or 20-day high proximity condition is met → price near recent high.
"""

#Configuration parameters for "near high" check
#Defines lookback windows (10 and 20 days) and tolerance (3 %).
@dataclass
class NearHighConfig:
    high_window_short: int = 10   # short-term high window
    high_window_long: int = 20    # longer-term high window
    tolerance: float = 0.03       # 3% under high counts as "near"

#Structured result object
#Holds booleans and metrics (percent distances, actual highs, close).
@dataclass
class NearHighResult:
    near_high: bool
    pct_from_high_10d: Optional[float]
    pct_from_high_20d: Optional[float]
    recent_high_10d: Optional[float]
    recent_high_20d: Optional[float]
    close: Optional[float]
    reason: Optional[str] = None


#Main logic — checks if today’s close is within tolerance of recent highs.
def price_near_recent_high(df: pd.DataFrame, cfg: NearHighConfig | None = None) -> NearHighResult:
    """Check whether price is within a few percent of recent highs (10d / 20d)."""
    if cfg is None:
        cfg = NearHighConfig()

    # Input validation
    if df is None or len(df) < max(cfg.high_window_long + 2, 30):
        return NearHighResult(False, None, None, None, None, None, "insufficient_bars")

    #gives recent resistance
    close = df["Close"].iloc[-1].item()
    recent_high_10d = df["High"].rolling(window=cfg.high_window_short).max().iloc[-1].item()
    recent_high_20d = df["High"].rolling(window=cfg.high_window_long).max().iloc[-1].item()


    #Compute % distance below each high
    pct_from_high_10d = (recent_high_10d - close) / recent_high_10d
    pct_from_high_20d = (recent_high_20d - close) / recent_high_20d

    #Condition: within tolerance (e.g., within 3% below the high)
    near_10d = 0 <= pct_from_high_10d <= cfg.tolerance
    near_20d = 0 <= pct_from_high_20d <= cfg.tolerance
    near_high = near_10d or near_20d

    return NearHighResult(
        near_high=bool(near_high),
        pct_from_high_10d=pct_from_high_10d,
        pct_from_high_20d=pct_from_high_20d,
        recent_high_10d=recent_high_10d,
        recent_high_20d=recent_high_20d,
        close=close,
        reason=None,
    )


def check_52_week_high_proximity(df: pd.DataFrame, tolerance: float = 0.15) -> dict:
    """
    Check how close price is to its 52-week high.
    
    Args:
        df: OHLCV dataframe (needs at least 252 days ideally)
        tolerance: max % below 52w high to be considered "near" (default 15%)
    
    Returns:
        dict with proximity metrics
    """
    if df is None or len(df) < 30:
        return {
            'week_52_high': None,
            'pct_from_52w_high': None,
            'near_52w_high': False,
            'reason': 'insufficient_bars'
        }

    # Use up to 252 trading days (1 year), whatever is available
    lookback = min(252, len(df))
    week_52_high = df['High'].tail(lookback).max()
    close = df['Close'].iloc[-1]
    
    pct_from_52w_high = (week_52_high - close) / week_52_high
    near_52w_high = pct_from_52w_high <= tolerance

    return {
        'week_52_high': round(week_52_high, 2),
        'pct_from_52w_high': round(pct_from_52w_high, 4),
        'near_52w_high': bool(near_52w_high)
    }

def check_compression(ticker: str, df: pd.DataFrame) -> dict:
    """
    Run all compression checks and return combined metrics.
    
    Args:
        ticker: stock symbol
        df: OHLCV dataframe
    
    Returns:
        dict with all compression metrics
    """
    atr_result = atr_compression(df)
    near_high_result = price_near_recent_high(df)
    week_52_result = check_52_week_high_proximity(df)

    return {
        'ticker': ticker,
        # ATR compression
        'atr_contracting': atr_result.contracting,
        'atr_today': atr_result.atr_today,
        'atr_lookback': atr_result.atr_lookback,
        # Near recent high
        'near_recent_high': near_high_result.near_high,
        'pct_from_high_10d': near_high_result.pct_from_high_10d,
        'pct_from_high_20d': near_high_result.pct_from_high_20d,
        # 52-week high
        'week_52_high': week_52_result['week_52_high'],
        'pct_from_52w_high': week_52_result['pct_from_52w_high'],
        'near_52w_high': week_52_result['near_52w_high']
    }