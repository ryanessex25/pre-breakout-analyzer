"""
STEP 2: Momentum Divergences (RSI / MACD / OBV)
Detects when indicators strengthen before price does (hidden accumulation)
"""

import pandas as pd
import numpy as np
import config
from utils import calculate_rsi, calculate_macd, calculate_obv, calculate_slope


def analyze_divergences(df):
    """
    Analyze momentum divergences in RSI, MACD, and OBV
    
    Criteria:
    - RSI rising over last 5 days while price flat or down
    - MACD histogram turning positive
    - OBV trending upward (5-day slope > 0)
    
    Args:
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: {
            'signal': bool,
            'score': float (0-10),
            'details': dict with breakdown
        }
    """
    
    try:
        if len(df) < 30:  # Need sufficient data for indicators
            return {
                'signal': False,
                'score': 0,
                'details': {'error': 'Insufficient data'}
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
        
        # Check RSI trend (last 5 days)
        rsi_slope = calculate_slope(df['RSI'], config.STEP2_RSI_LOOKBACK)
        rsi_rising = rsi_slope > 0
        
        # Check price trend (last 5 days)
        price_slope = calculate_slope(df['Close'], config.STEP2_RSI_LOOKBACK)
        price_flat_or_down = price_slope <= 0.5  # Slightly positive is ok
        
        # RSI divergence: RSI rising while price not rising much
        rsi_divergence = rsi_rising and price_flat_or_down
        
        # MACD histogram check
        current_histogram = df['MACD_histogram'].iloc[-1]
        prev_histogram = df['MACD_histogram'].iloc[-2]
        macd_turning_positive = current_histogram > 0 or (current_histogram > prev_histogram and prev_histogram < 0)
        
        # OBV trend check
        obv_slope = calculate_slope(df['OBV'], config.STEP2_OBV_LOOKBACK)
        obv_rising = obv_slope > 0
        
        # Scoring logic (0-10)
        score = 0
        
        # RSI divergence (0-4 points)
        if rsi_divergence:
            if rsi_slope > 3:  # Strong divergence
                score += 4
            elif rsi_slope > 2:
                score += 3
            elif rsi_slope > 1:
                score += 2
        
        # MACD component (0-3 points)
        if macd_turning_positive:
            if current_histogram > 1:
                score += 3
            elif current_histogram > 0:
                score += 1
        
        # OBV component (0-3 points)
        if obv_rising:
            if obv_slope > np.percentile(df['OBV'].diff(), 85):  # Strong OBV increase
                score += 3
            elif obv_slope > np.percentile(df['OBV'].diff(), 70):
                score += 2
        
        # Signal triggers if score >= 5
        signal_triggered = score >= 7
        
        details = {
            'rsi_current': round(df['RSI'].iloc[-1], 2),
            'rsi_slope': round(rsi_slope, 3),
            'rsi_divergence': rsi_divergence,
            'macd_histogram': round(current_histogram, 4),
            'macd_turning_positive': macd_turning_positive,
            'obv_slope': round(obv_slope, 0),
            'obv_rising': obv_rising,
            'price_slope': round(price_slope, 3)
        }
        
        return {
            'signal': signal_triggered,
            'score': score,
            'details': details
        }
    
    except Exception as e:
        return {
            'signal': False,
            'score': 0,
            'details': {'error': str(e)}
        }


def check_step2(ticker, df):
    """
    Wrapper function for Step 2 analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Analysis results
    """
    result = analyze_divergences(df)
    result['ticker'] = ticker
    result['step'] = 'Step 2: Divergences'
    
    return result