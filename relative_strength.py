"""
STEP 3: Relative Strength vs Sector or Market
Detects when stock outperforms SPY (smart money signal)
UPDATED: Focus on EARLY outperformance and turning points, not established strength
"""

import pandas as pd
import config
from utils import calculate_slope


def analyze_relative_strength(df, spy_df):
    """
    Analyze relative strength vs SPY
    
    UPDATED CRITERIA FOR EARLY DETECTION:
    - RS slope just turned positive (turning point)
    - Reward SMALL outperformance (0-5%) over large (>10%)
    - Detect recent RS improvement (last 2-3 days)
    - PENALIZE stocks already up 20%+ (too late)
    
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
        
        if len(df) < config.STEP3_RS_LOOKBACK + 5 or len(spy_df) < config.STEP3_RS_LOOKBACK + 5:
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
        
        if len(aligned_df) < config.STEP3_RS_LOOKBACK:
            return {
                'signal': False,
                'score': 0,
                'details': {'error': 'Insufficient aligned data'}
            }
        
        # Calculate RS ratio (Stock / SPY)
        aligned_df['rs_ratio'] = aligned_df['stock_close'] / aligned_df['spy_close']
        
        # Calculate RS slope over 5 days
        rs_slope = calculate_slope(aligned_df['rs_ratio'], config.STEP3_RS_LOOKBACK)
        
        # Calculate RS slope over last 2-3 days (recent turning point)
        rs_slope_recent = calculate_slope(aligned_df['rs_ratio'], 3)
        
        # Check if RS just turned positive (was negative, now positive)
        rs_slope_prev = calculate_slope(aligned_df['rs_ratio'].iloc[:-1], 3)
        rs_just_turned_positive = (rs_slope_recent > 0 and rs_slope_prev <= 0)
        
        # Calculate percentage change in RS over period
        rs_current = aligned_df['rs_ratio'].iloc[-1]
        rs_past = aligned_df['rs_ratio'].iloc[-config.STEP3_RS_LOOKBACK]
        rs_change_pct = ((rs_current - rs_past) / rs_past) * 100 if rs_past != 0 else 0
        
        # Calculate stock vs SPY performance over 5 days
        stock_change = ((aligned_df['stock_close'].iloc[-1] - aligned_df['stock_close'].iloc[-config.STEP3_RS_LOOKBACK]) 
                       / aligned_df['stock_close'].iloc[-config.STEP3_RS_LOOKBACK] * 100)
        spy_change = ((aligned_df['spy_close'].iloc[-1] - aligned_df['spy_close'].iloc[-config.STEP3_RS_LOOKBACK]) 
                     / aligned_df['spy_close'].iloc[-config.STEP3_RS_LOOKBACK] * 100)
        
        outperformance = stock_change - spy_change
        
        # Calculate stock performance over longer period (20 days) to check if already extended
        lookback_20d = min(20, len(aligned_df))
        stock_change_20d = ((aligned_df['stock_close'].iloc[-1] - aligned_df['stock_close'].iloc[-lookback_20d]) 
                           / aligned_df['stock_close'].iloc[-lookback_20d] * 100)
        
        
        # Scoring logic (0-10) - FOCUS ON EARLY TURNING POINTS
        score = 0
        
        """
        Component 1: RS Slope Turning Point (0-4 points)
            PERFECT: Just caught the turn from negative to positive
            GOOD: Positive and accelerating recently
            OK: Positive but not accelerating
            EARLY: Almost turning positive (very small negative)
            Negative slope - not ready yet
        """
        if rs_just_turned_positive:
            score += 4
        elif rs_slope > 0 and rs_slope_recent > rs_slope:
            score += 3
        elif rs_slope > 0:
            score += 2
        elif rs_slope > -0.0001:
            score += 1
        else:
            score += 0
        


        """
        Component 2: Outperformance Sweet Spot (0-2 points)
            GOOD: Moderate outperformance (3-5%)
            OK: Getting extended (5-8%)
            LATE: Already moved significantly (8-12%)
            TOO LATE: Big move already happened (>12%)        
        """
        if 0 <= outperformance <= 3:
            score += 2
        elif 3 < outperformance <= 5:
            score += 1
        else:
            score += 0
        


        """
        Component 3: Extended Move Check
            Check 20-day performance to avoid stocks that already ran
            Sweet spot: Stock up 0-10% (fresh, early)
            Either down (not ready) or up >10% (too late)
        """
        if 0 <= stock_change_20d <= 10:  
            score += 4
        else:
            score += 0
      
        
        # Signal triggers if score >= 6 (Slightly more flexible threshold)
        signal_triggered = score >= 7

        
        details = {
            'rs_ratio_current': round(rs_current, 6),
            'rs_slope': round(rs_slope, 8),
            'rs_slope_recent': round(rs_slope_recent, 8),
            'rs_just_turned_positive': rs_just_turned_positive,
            'rs_change_pct': round(rs_change_pct, 2),
            'stock_change_pct': round(stock_change, 2),
            'spy_change_pct': round(spy_change, 2),
            'outperformance': round(outperformance, 2),
            'stock_change_20d': round(stock_change_20d, 2),
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


def check_step3(ticker, df, spy_df):
    """
    Wrapper function for Step 3 analysis
    
    Args:
        ticker (str): Stock symbol
        df (pd.DataFrame): Stock OHLCV data
        spy_df (pd.DataFrame): SPY OHLCV data
    
    Returns:
        dict: Analysis results
    """
    result = analyze_relative_strength(df, spy_df)
    result['ticker'] = ticker
    result['step'] = 'Step 3: Relative Strength'
    
    return result