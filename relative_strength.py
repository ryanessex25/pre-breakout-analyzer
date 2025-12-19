"""
STEP 7: Relative Strength vs Sector or Market
Detects when stock outperforms SPY (smart money signal)
"""

import pandas as pd
import config
from utils import calculate_slope


def analyze_relative_strength(df, spy_df):
    """
    Analyze relative strength vs SPY
    
    Criteria:
    - (Stock close / SPY close) ratio increasing
    - 5-day RS slope > 0
    
    Args:
        df (pd.DataFrame): Stock OHLCV data
        spy_df (pd.DataFrame): SPY OHLCV data
    
    Returns:
        dict: {
            'signal': bool,
            'score': float (0-10),
            'details': dict with breakdown
        }
    """
    
    try:
        if df is None or spy_df is None:
            return {
                'signal': False,
                'score': 0,
                'details': {'error': 'Missing data'}
            }
        
        if len(df) < config.STEP7_RS_LOOKBACK + 5 or len(spy_df) < config.STEP7_RS_LOOKBACK + 5:
            return {
                'signal': False,
                'score': 0,
                'details': {'error': 'Insufficient data'}
            }
        
        # Align dataframes by date
        aligned_df = pd.DataFrame({
            'stock_close': df['Close'],
            'spy_close': spy_df['Close']
        }).dropna()
        
        if len(aligned_df) < config.STEP7_RS_LOOKBACK:
            return {
                'signal': False,
                'score': 0,
                'details': {'error': 'Insufficient aligned data'}
            }
        
        # Calculate RS ratio (Stock / SPY)
        aligned_df['rs_ratio'] = aligned_df['stock_close'] / aligned_df['spy_close']
        
        # Calculate RS slope
        rs_slope = calculate_slope(aligned_df['rs_ratio'], config.STEP7_RS_LOOKBACK)
        
        # Calculate percentage change in RS over period
        rs_current = aligned_df['rs_ratio'].iloc[-1]
        rs_past = aligned_df['rs_ratio'].iloc[-config.STEP7_RS_LOOKBACK]
        rs_change_pct = ((rs_current - rs_past) / rs_past) * 100 if rs_past != 0 else 0
        
        # Calculate stock vs SPY performance
        stock_change = ((aligned_df['stock_close'].iloc[-1] - aligned_df['stock_close'].iloc[-config.STEP7_RS_LOOKBACK]) 
                       / aligned_df['stock_close'].iloc[-config.STEP7_RS_LOOKBACK] * 100)
        spy_change = ((aligned_df['spy_close'].iloc[-1] - aligned_df['spy_close'].iloc[-config.STEP7_RS_LOOKBACK]) 
                     / aligned_df['spy_close'].iloc[-config.STEP7_RS_LOOKBACK] * 100)
        
        outperformance = stock_change - spy_change
        
        # Scoring logic (0-10)
        score = 0
        
        # RS slope component (0-5 points)
        if rs_slope > 0:
            if rs_change_pct > 3:  # Strong outperformance
                score += 5
            elif rs_change_pct > 1:
                score += 4
            elif rs_change_pct > 0.3:
                score += 3
            else:
                score += 2
        
        # Outperformance component (0-5 points)
        if outperformance > 5:  # Significantly outperforming
            score += 5
        elif outperformance > 2:
            score += 4
        elif outperformance > 0:
            score += 3
        elif outperformance > -2:  # Slightly underperforming is ok if RS slope positive
            score += 1
        
        # Signal triggers if score >= 5
        signal_triggered = score >= 5
        
        details = {
            'rs_ratio_current': round(rs_current, 6),
            'rs_slope': round(rs_slope, 8),
            'rs_change_pct': round(rs_change_pct, 2),
            'stock_change_pct': round(stock_change, 2),
            'spy_change_pct': round(spy_change, 2),
            'outperformance': round(outperformance, 2),
            'rs_increasing': rs_slope > 0
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


def check_step7(ticker, df, spy_df):
    """
    Wrapper function for Step 7 analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): Stock OHLCV data
        spy_df (pd.DataFrame): SPY OHLCV data
    
    Returns:
        dict: Analysis results
    """
    result = analyze_relative_strength(df, spy_df)
    result['ticker'] = ticker
    result['step'] = 'Step 7: Relative Strength'
    
    return result