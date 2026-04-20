from __future__ import annotations 
import numpy as np 
import pandas as pd 

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
