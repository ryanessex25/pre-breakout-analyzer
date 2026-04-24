"""
Utility functions for technical indicators and calculations.

"""

import pandas as pd
import numpy as np
from __future__ import annotations 
import numpy as np 

def calculate_ema(data, period):
    """
    Calculate Exponential Moving Average
    
    Args:
        data (pd.Series): Price data
        period (int): EMA period
    
    Returns:
        pd.Series: EMA values
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    #Wilder (standard for RSI)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(data, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        data (pd.Series): Price data
        fast (int): Fast EMA period
        slow (int): Slow EMA period
        signal (int): Signal line period
    
    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_obv(df):
    """
    Calculate On-Balance Volume
    
    Args:
        df (pd.DataFrame): OHLCV dataframe
    
    Returns:
        pd.Series: OBV values
    """
    obv = pd.Series(index=df.index, dtype=float)
    obv.iloc[0] = df['Volume'].iloc[0]
    
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + df['Volume'].iloc[i]
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - df['Volume'].iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv


def calculate_slope(series, periods):
    """
    Calculate the slope of a series over the last N periods
    
    Args:
        series (pd.Series): Data series
        periods (int): Number of periods to calculate slope
    
    Returns:
        float: Slope value (positive = uptrend, negative = downtrend)
    """
    if len(series) < periods:
        return 0
    
    # Get last N values
    y = series.tail(periods).values
    x = np.arange(len(y))
    
    # Calculate slope using linear regression
    if len(x) < 2:
        return 0
    
    slope = np.polyfit(x, y, 1)[0]
    return slope


def is_red_day(df, index):
    """
    Check if a specific day is a red (down) day
    
    Args:
        df (pd.DataFrame): OHLCV dataframe
        index (int): Index position
    
    Returns:
        bool: True if red day, False otherwise
    """
    if index >= len(df):
        return False
    
    return df['Close'].iloc[index] < df['Open'].iloc[index]


def get_red_day_avg_volume(df, lookback=20):
    """
    Calculate average volume on red (down) days
    
    Args:
        df (pd.DataFrame): OHLCV dataframe
        lookback (int): Number of days to look back
    
    Returns:
        float: Average volume on red days
    """
    if len(df) < lookback:
        lookback = len(df)
    
    recent_data = df.tail(lookback).copy()
    recent_data['is_red'] = recent_data['Close'] < recent_data['Open']
    
    red_day_volumes = recent_data[recent_data['is_red']]['Volume']
    
    if len(red_day_volumes) == 0:
        return recent_data['Volume'].mean()  # Fallback to overall average
    
    return red_day_volumes.mean()

# Expected DataFrame columns:
# ['Open', 'High', 'Low', 'Close', 'Volume']
# Indexed by datetime.

def true_range(df: pd.DataFrame) -> pd.Series:
    """
    Compute the True Range for each bar.

    True Range = max(
        High - Low,
        abs(High - Previous Close),
        abs(Low - Previous Close)
    )
    Captures the total movement including overnight gaps.
    """
    prev_close = df["Close"].shift(1) #moves the Close column down one row so each day can reference yesterday’s close.
    high_low = df["High"] - df["Low"] #Normal daily range.
    high_pc = (df["High"] - prev_close).abs() #Distance between today’s high and yesterday’s close (captures upward gaps).
    low_pc = (df["Low"] - prev_close).abs() #Distance between today’s low and yesterday’s close (captures downward gaps).
    return pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1) #Takes the maximum of those three distances — the True Range (TR) for each day.


def atr(df: pd.DataFrame, period: int = 14, use_ema: bool = True) -> pd.Series:
    """
    Calculate the Average True Range (ATR).
    By default uses Wilder’s EMA smoothing with alpha = 1/period.
    """
    tr = true_range(df)

    if use_ema:
        # Wilder-style exponential moving average
        return tr.ewm(alpha=1 / period, adjust=False).mean()
    else:
        # Simple moving average
        return tr.rolling(window=period, min_periods=period).mean()
