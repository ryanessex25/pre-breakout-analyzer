"""
Relative Strength Analysis Module
Extracts relative strength metrics vs SPY - no scoring logic
"""

import pandas as pd
import config
from utils import calculate_slope


def analyze_relative_strength(df, spy_df):
    """
    Extract relative strength metrics vs SPY
    
    Args:
        df (pd.DataFrame): Stock OHLCV data
        spy_df (pd.DataFrame): SPY OHLCV data
    
    Returns:
        dict: Raw RS metrics (no scoring)
    """
    
    try:
        if df is None or spy_df is None:
            return {
                'error': 'Missing data',
                'rs_slope': 0,
                'outperformance': 0
            }
        
        if len(df) < config.STEP3_RS_LOOKBACK + 5 or len(spy_df) < config.STEP3_RS_LOOKBACK + 5:
            return {
                'error': 'Insufficient data',
                'rs_slope': 0,
                'outperformance': 0
            }
        
        # Align dataframes by date
        aligned_df = pd.DataFrame({
            'stock_close': df['Close'],
            'spy_close': spy_df['Close']
        }).dropna()
        
        if len(aligned_df) < config.STEP3_RS_LOOKBACK:
            return {
                'error': 'Insufficient aligned data',
                'rs_slope': 0,
                'outperformance': 0
            }
        
        # Calculate RS ratio (Stock / SPY)
        aligned_df['rs_ratio'] = aligned_df['stock_close'] / aligned_df['spy_close']
        
        # Calculate RS slope over 5 days
        rs_slope = calculate_slope(aligned_df['rs_ratio'], config.STEP3_RS_LOOKBACK)
        
        # Calculate stock vs SPY performance over 5 days
        stock_change = ((aligned_df['stock_close'].iloc[-1] - aligned_df['stock_close'].iloc[-config.STEP3_RS_LOOKBACK]) 
                       / aligned_df['stock_close'].iloc[-config.STEP3_RS_LOOKBACK] * 100)
        spy_change = ((aligned_df['spy_close'].iloc[-1] - aligned_df['spy_close'].iloc[-config.STEP3_RS_LOOKBACK]) 
                     / aligned_df['spy_close'].iloc[-config.STEP3_RS_LOOKBACK] * 100)
        
        outperformance = stock_change - spy_change
        
        # Return raw metrics only (no scoring)
        return {
            'rs_slope': round(rs_slope, 8),
            'outperformance': round(outperformance, 2)
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'rs_slope': 0,
            'outperformance': 0
        }


def check_step3(ticker, df, spy_df):
    """
    Wrapper function for relative strength analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): Stock OHLCV data
        spy_df (pd.DataFrame): SPY OHLCV data
    
    Returns:
        dict: RS metrics with ticker
    """
    metrics = analyze_relative_strength(df, spy_df)
    metrics['ticker'] = ticker
    
    return metrics