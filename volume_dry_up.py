"""
STEP 1: Volume Dry-Up During Pullback
Detects when pullbacks occur on lighter volume (no aggressive selling)
"""

import pandas as pd
import config
from utils import calculate_ema, get_red_day_avg_volume


def analyze_volume_dryup(df):
    """
    Analyze if stock shows volume dry-up during pullback
    
    Criteria:
    - Average volume on red days < 0.7x 20-day average
    - Price stays above 21 EMA during pullback
    
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
        if len(df) < config.STEP1_LOOKBACK_PERIOD + 5:
            return {
                'signal': False,
                'score': 0,
                'details': {'error': 'Insufficient data'}
            }
        
        # Calculate 21 EMA
        df['EMA_21'] = calculate_ema(df['Close'], config.STEP1_EMA_PERIOD)
        
        # Get 20-day average volume
        avg_volume_20d = df['Volume'].tail(config.STEP1_LOOKBACK_PERIOD).mean()
        
        # Get average volume on red days
        red_day_avg_volume = get_red_day_avg_volume(df, config.STEP1_LOOKBACK_PERIOD)
        
        # Calculate ratio
        red_volume_ratio = red_day_avg_volume / avg_volume_20d if avg_volume_20d > 0 else 1
        
        # Check if price is above 21 EMA (last 3 days)
        recent_prices = df['Close'].tail(3)
        recent_ema = df['EMA_21'].tail(3)
        price_above_ema = (recent_prices > recent_ema).sum() >= 2  # At least 2 out of 3 days
        
        # Scoring logic
        score = 0
        
        # Volume dry-up component (0-7 points)
        if red_volume_ratio < 0.4:
            score += 7
        elif red_volume_ratio < 0.5:
            score += 6
        elif red_volume_ratio < 0.6:
            score += 4
        elif red_volume_ratio < 0.7:
            score += 2
        
        # Price above EMA component (0-3 points)
        if price_above_ema:
            score += 3
        
        # Signal triggers if score >= 5
        signal_triggered = score >= 7
        
        details = {
            'red_day_avg_volume': round(red_day_avg_volume, 0),
            '20d_avg_volume': round(avg_volume_20d, 0),
            'red_volume_ratio': round(red_volume_ratio, 3),
            'price_above_ema_21': price_above_ema,
            'current_price': round(df['Close'].iloc[-1], 2),
            'ema_21': round(df['EMA_21'].iloc[-1], 2)
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


def check_step1(ticker, df):
    """
    Wrapper function for Step 1 analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Analysis results
    """
    result = analyze_volume_dryup(df)
    result['ticker'] = ticker
    result['step'] = 'Step 1: Volume Dry-Up'
    
    return result