"""
STEP 2: Momentum Divergences (RSI / MACD / OBV)
Detects when indicators strengthen before price does (hidden accumulation)
UPDATED: Focus on EARLY accumulation phase (RSI 40-65, not overbought)
"""

import pandas as pd
import numpy as np
import config
from utils import calculate_rsi, calculate_macd, calculate_obv, calculate_slope


def analyze_divergences(df):
    """
    Analyze momentum divergences in RSI, MACD, and OBV
    
    UPDATED CRITERIA FOR EARLY DETECTION:
    - RSI between 40-65 (building strength, not overbought)
    - MACD histogram negative but improving (turning point)
    - OBV trending upward (accumulation)
    - PENALIZE RSI > 70 (that's too late)
    
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
        
        # MACD histogram check - separate early vs late signals
        current_histogram = df['MACD_histogram'].iloc[-1]
        prev_histogram = df['MACD_histogram'].iloc[-2]
        
        # Early signal: histogram negative but improving (WHAT WE WANT)
        macd_improving_from_negative = current_histogram > prev_histogram and current_histogram < 0
        
        # Late signal: histogram already positive
        macd_histogram_positive = current_histogram > 0
        
        # Combined for backwards compatibility
        macd_turning_positive = macd_histogram_positive or macd_improving_from_negative
        
        # OBV trend check
        obv_slope = calculate_slope(df['OBV'], config.STEP2_OBV_LOOKBACK)
        obv_rising = obv_slope > 0
        
        # Get current RSI value
        current_rsi = df['RSI'].iloc[-1]
        
        # Scoring logic (0-10) - EARLY ACCUMULATION FOCUS
        score = 0
        
        # RSI component (0-5 points) - REWARD EARLY STRENGTH (40-65), PENALIZE OVERBOUGHT (>70)
        if 40 <= current_rsi <= 65:
            # SWEET SPOT - this is the BEST zone (max 5 points)
            if rsi_divergence and rsi_slope > 2:
                score += 5  # Perfect: strong divergence in ideal range
            elif rsi_divergence and rsi_slope > 1:
                score += 4  # Great: good divergence in ideal range
            elif rsi_rising:
                score += 3  # Good: RSI rising in accumulation zone
            else:
                score += 2  # Okay: in good range but not doing much
        elif 35 <= current_rsi < 40:
            # EARLY RECOVERY - might be too early (max 2 points)
            if rsi_rising:
                score += 2  # Rising from oversold
            else:
                score += 0  # Too early and not even rising
        elif 65 < current_rsi <= 70:
            # GETTING EXTENDED - starting to get late (max 1 point)
            if rsi_divergence:
                score += 1  # Still has divergence but getting extended
            else:
                score += 0  # Just momentum, getting late
        elif current_rsi > 70:
            # TOO LATE - already overbought (0 points)
            score += 0  # We missed the early entry
        

        # MACD component (0-3 points) - Focus on turning points
        if macd_improving_from_negative:
           # Best: Histogram negative but improving (catching BEFORE the turn)
            score += 3
        elif macd_histogram_positive and current_histogram < 0.2:
           # Good: Just turned positive very recently (within small threshold)
            score += 2
        else:
            # Everything else gets zero (already extended or not improving)
            score += 0
        

        # OBV component (0-2 points) - ACCUMULATION SIGNAL
        if obv_rising:
            if obv_slope > np.percentile(df['OBV'].diff(), 75):  # Strong accumulation
                score += 2
            else:
                score += 1

        
        # Signal triggers if score >= 7
        signal_triggered = score >= 6
        
        details = {
            'rsi_current': round(df['RSI'].iloc[-1], 2),
            'rsi_slope': round(rsi_slope, 3),
            'rsi_divergence': rsi_divergence,
            'macd_histogram': round(current_histogram, 4),
            'macd_histogram_prev': round(prev_histogram, 4),
            'macd_improving_from_negative': macd_improving_from_negative,
            'macd_histogram_positive': macd_histogram_positive,
            'macd_turning_positive': macd_turning_positive,
            'obv_slope': round(obv_slope, 0),
            'obv_rising': obv_rising,
            'price_slope': round(price_slope, 3),
            'rsi_in_accumulation_zone': 40 <= current_rsi <= 65
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