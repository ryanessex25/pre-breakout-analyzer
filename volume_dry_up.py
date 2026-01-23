"""
Volume Analysis Module
Extracts volume metrics - no scoring logic
"""

import pandas as pd
import config
from utils import calculate_ema, get_red_day_avg_volume


def analyze_volume_dryup(df):
    """
    Extract volume metrics from stock data
    
    Args:
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Raw volume metrics (no scoring)
    """
    
    try:
        if len(df) < config.STEP1_LOOKBACK_PERIOD + 5:
            return {
                'error': 'Insufficient data',
                'red_volume_ratio': 1.0,
                'price_above_ema': False,
                'red_day_avg_volume': 0,
                'green_day_avg_volume': 0,
                '20d_avg_volume': 0,
                'red_day_count': 0,
                'green_day_count': 0,
                'current_price': 0,
                'ema_21': 0
            }
        
        # Calculate 21 EMA
        df['EMA_21'] = calculate_ema(df['Close'], config.STEP1_EMA_PERIOD)
        
        # Get 20-day average volume
        avg_volume_20d = df['Volume'].tail(config.STEP1_LOOKBACK_PERIOD).mean()
        
        # Get average volume on red days
        red_day_avg_volume = get_red_day_avg_volume(df, config.STEP1_LOOKBACK_PERIOD)
        
        # Calculate ratio
        red_volume_ratio = red_day_avg_volume / avg_volume_20d if avg_volume_20d > 0 else 1
        
        # Calculate red/green day counts and volumes
        recent_data = df.tail(config.STEP1_LOOKBACK_PERIOD).copy()
        recent_data['is_red'] = recent_data['Close'] < recent_data['Open']
        recent_data['is_green'] = recent_data['Close'] >= recent_data['Open']
        
        red_days = recent_data[recent_data['is_red']]
        green_days = recent_data[recent_data['is_green']]
        
        red_day_count = len(red_days)
        green_day_count = len(green_days)
        green_day_avg_volume = green_days['Volume'].mean() if len(green_days) > 0 else avg_volume_20d
        
        # Check if price is above 21 EMA (last 3 days)
        recent_prices = df['Close'].tail(3)
        recent_ema = df['EMA_21'].tail(3)
        price_above_ema = (recent_prices > recent_ema).sum() >= 2  # At least 2 out of 3 days
        
        # Return raw metrics only (no scoring)
        return {
            'red_volume_ratio': round(red_volume_ratio, 3),
            'price_above_ema': price_above_ema,
            'red_day_avg_volume': round(red_day_avg_volume, 0),
            'green_day_avg_volume': round(green_day_avg_volume, 0),
            '20d_avg_volume': round(avg_volume_20d, 0),
            'red_day_count': red_day_count,
            'green_day_count': green_day_count,
            'current_price': round(df['Close'].iloc[-1], 2),
            'ema_21': round(df['EMA_21'].iloc[-1], 2)
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'red_volume_ratio': 1.0,
            'price_above_ema': False,
            'red_day_avg_volume': 0,
            'green_day_avg_volume': 0,
            '20d_avg_volume': 0,
            'red_day_count': 0,
            'green_day_count': 0,
            'current_price': 0,
            'ema_21': 0
        }


def check_step1(ticker, df):
    """
    Wrapper function for volume analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Volume metrics with ticker
    """
    metrics = analyze_volume_dryup(df)
    metrics['ticker'] = ticker
    
    return metrics