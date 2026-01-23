"""
Momentum Analysis Module
Extracts momentum metrics (RSI, MACD, OBV) - no scoring logic
"""

import pandas as pd
import numpy as np
import config
from utils import calculate_rsi, calculate_macd, calculate_obv, calculate_slope


def analyze_divergences(df):
    """
    Extract momentum metrics from stock data
    
    Args:
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Raw momentum metrics (no scoring)
    """
    
    try:
        if len(df) < 30:  # Need sufficient data for indicators
            return {
                'error': 'Insufficient data',
                'rsi_current': 50,
                'rsi_slope': 0,
                'price_slope': 0,
                'macd_histogram': 0,
                'macd_histogram_prev': 0,
                'obv_days_rising': 0
            }
        
        # Calculate indicators
        df['RSI'] = calculate_rsi(df['Close'], config.STEP2_RSI_PERIOD)
        macd_line, signal_line, histogram = calculate_macd(
            df['Close'], 
            config.STEP2_MACD_FAST, 
            config.STEP2_MACD_SLOW, 
            config.STEP2_MACD_SIGNAL
        )
        df['MACD_histogram'] = histogram
        df['OBV'] = calculate_obv(df)
        
        # RSI metrics
        rsi_current = df['RSI'].iloc[-1]
        rsi_slope = calculate_slope(df['RSI'], config.STEP2_RSI_LOOKBACK)
        
        # Price slope (for divergence detection)
        price_slope = calculate_slope(df['Close'], config.STEP2_RSI_LOOKBACK)
        
        # MACD metrics
        current_histogram = df['MACD_histogram'].iloc[-1]
        prev_histogram = df['MACD_histogram'].iloc[-2]
        
        # OBV consistency - count how many days OBV increased in last 5 days
        obv_changes = df['OBV'].tail(6).diff()  # 6 to get 5 diffs
        obv_days_rising = (obv_changes.tail(5) > 0).sum()  # Count positive days
        
        # Return raw metrics only (no scoring)
        return {
            'rsi_current': round(rsi_current, 2),
            'rsi_slope': round(rsi_slope, 3),
            'price_slope': round(price_slope, 3),
            'macd_histogram': round(current_histogram, 4),
            'macd_histogram_prev': round(prev_histogram, 4),
            'obv_days_rising': int(obv_days_rising)
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'rsi_current': 50,
            'rsi_slope': 0,
            'price_slope': 0,
            'macd_histogram': 0,
            'macd_histogram_prev': 0,
            'obv_days_rising': 0
        }


def check_step2(ticker, df):
    """
    Wrapper function for momentum analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Momentum metrics with ticker
    """
    metrics = analyze_divergences(df)
    metrics['ticker'] = ticker
    
    return metrics