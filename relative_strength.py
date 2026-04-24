"""
Relative Strength Analysis Module
Extracts relative strength metrics vs SPY - no scoring logic
"""

import pandas as pd
import config
from utility_calculations import calculate_slope


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
                'rs_slope_short': 0,
                'rs_slope_long': 0,
                'outperformance_short': 0,
                'outperformance_long': 0
            }
        
        min_required = config.RS_LOOKBACK_LONG + 5
        if len(df) < min_required or len(spy_df) < min_required:
            return {
                'error': 'Insufficient data',
                'rs_slope_short': 0,
                'rs_slope_long': 0,
                'outperformance_short': 0,
                'outperformance_long': 0
            }
        
        # Align dataframes by date
        aligned_df = pd.DataFrame({
            'stock_close': df['Close'],
            'spy_close': spy_df['Close']
        }).dropna()
        
        if len(aligned_df) < min_required:
            return {
                'error': 'Insufficient aligned data',
                'rs_slope_short': 0,
                'rs_slope_long': 0,
                'outperformance_short': 0,
                'outperformance_long': 0
            }
        
        # Calculate RS ratio (Stock / SPY)
        aligned_df['rs_ratio'] = aligned_df['stock_close'] / aligned_df['spy_close']
        
        # Short-term RS (10 days / 2 weeks)
        rs_slope_short = calculate_slope(aligned_df['rs_ratio'], config.RS_LOOKBACK_SHORT)
        
        stock_change_short = ((aligned_df['stock_close'].iloc[-1] - aligned_df['stock_close'].iloc[-config.RS_LOOKBACK_SHORT]) 
                              / aligned_df['stock_close'].iloc[-config.RS_LOOKBACK_SHORT] * 100)
        spy_change_short = ((aligned_df['spy_close'].iloc[-1] - aligned_df['spy_close'].iloc[-config.RS_LOOKBACK_SHORT]) 
                            / aligned_df['spy_close'].iloc[-config.RS_LOOKBACK_SHORT] * 100)
        outperformance_short = stock_change_short - spy_change_short

        #  Long-term RS (60 days / 3 months) 
        rs_slope_long = calculate_slope(aligned_df['rs_ratio'], config.RS_LOOKBACK_LONG)

        stock_change_long = ((aligned_df['stock_close'].iloc[-1] - aligned_df['stock_close'].iloc[-config.RS_LOOKBACK_LONG]) 
                             / aligned_df['stock_close'].iloc[-config.RS_LOOKBACK_LONG] * 100)
        spy_change_long = ((aligned_df['spy_close'].iloc[-1] - aligned_df['spy_close'].iloc[-config.RS_LOOKBACK_LONG]) 
                           / aligned_df['spy_close'].iloc[-config.RS_LOOKBACK_LONG] * 100)
        outperformance_long = stock_change_long - spy_change_long

        return {
            'rs_slope_short': round(rs_slope_short, 8),
            'rs_slope_long': round(rs_slope_long, 8),
            'outperformance_short': round(outperformance_short, 2),
            'outperformance_long': round(outperformance_long, 2)
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'rs_slope_short': 0,
            'rs_slope_long': 0,
            'outperformance_short': 0,
            'outperformance_long': 0
        }


def check_relative_strength(ticker, df, spy_df):
    """
    Wrapper function for momentum analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): OHLCV data
    
    Returns:
        dict: Momentum metrics with ticker
    """
    metrics = analyze_relative_strength(df, spy_df)
    metrics['ticker'] = ticker
    return metrics