"""
Scoring System for Early Breakout Scanner
Cumulative point-based system with weighted metrics

Total Points Available: 35
- Volume Metrics: 15 points max
- Momentum Metrics: 12 points max
- Relative Strength Metrics: 8 points max

Alert Thresholds:
- 20+ points = High Priority Alert
- 15-19 points = Watch List
- <15 points = Skip
"""


def calculate_volume_score(metrics):
    """
    Calculate volume-based score (0-15 points)
    
    Args:
        metrics (dict): Volume metrics from volume_dry_up analysis
            - red_volume_ratio: float
            - price_above_ema: bool
            - red_day_avg_volume: float
            - green_day_avg_volume: float
    
    Returns:
        dict: {
            'total_score': int (0-15),
            'breakdown': dict with point details
        }
    """
    score = 0
    breakdown = {}
    
    # Red Volume Ratio (0-10 points)
    ratio = metrics.get('red_volume_ratio', 1.0)
    
    if ratio < 0.15:
        ratio_points = 10
        ratio_quality = "Exceptional"
    elif ratio < 0.30:
        ratio_points = 8
        ratio_quality = "Outstanding"
    elif ratio < 0.50:
        ratio_points = 6
        ratio_quality = "Strong"
    elif ratio < 0.70:
        ratio_points = 4
        ratio_quality = "Moderate"
    elif ratio < 0.85:
        ratio_points = 2
        ratio_quality = "Slight edge"
    else:
        ratio_points = 0
        ratio_quality = "No dry-up"
    
    score += ratio_points
    breakdown['red_volume_ratio'] = {
        'points': ratio_points,
        'value': ratio,
        'quality': ratio_quality
    }
    
    # Price Above 21 EMA (0-3 points)
    price_above_ema = metrics.get('price_above_ema', False)
    ema_points = 3 if price_above_ema else 0
    
    score += ema_points
    breakdown['price_above_ema'] = {
        'points': ema_points,
        'value': price_above_ema
    }
    
    # Red/Green Volume Spread (0-2 points)
    red_avg = metrics.get('red_day_avg_volume', 0)
    green_avg = metrics.get('green_day_avg_volume', 1)
    
    if red_avg > 0 and green_avg > 0:
        spread_ratio = green_avg / red_avg
        
        if spread_ratio > 2.0:
            spread_points = 2
            spread_quality = "Huge spread"
        elif spread_ratio > 1.5:
            spread_points = 1
            spread_quality = "Good spread"
        else:
            spread_points = 0
            spread_quality = "Minimal spread"
    else:
        spread_points = 0
        spread_ratio = 0
        spread_quality = "No data"
    
    score += spread_points
    breakdown['red_green_spread'] = {
        'points': spread_points,
        'ratio': spread_ratio,
        'quality': spread_quality
    }
    
    return {
        'total_score': score,
        'max_score': 15,
        'breakdown': breakdown
    }


def calculate_momentum_score(metrics):
    """
    Calculate momentum-based score (0-12 points)
    
    Args:
        metrics (dict): Momentum metrics from divergences analysis
            - rsi_slope: float
            - rsi_current: float
            - macd_histogram: float
            - macd_histogram_prev: float
            - obv_days_rising: int (out of 5)
    
    Returns:
        dict: {
            'total_score': int (0-12),
            'breakdown': dict with point details
        }
    """
    score = 0
    breakdown = {}
    
    # RSI Divergence (0-4 points)
    rsi_slope = metrics.get('rsi_slope', 0)
    price_slope = metrics.get('price_slope', 0)
    
    # Check for divergence (RSI rising while price flat/down)
    has_divergence = rsi_slope > 0 and price_slope <= 0.5
    
    if has_divergence:
        if rsi_slope > 2:
            divergence_points = 4
            divergence_quality = "Strong"
        elif rsi_slope > 1:
            divergence_points = 3
            divergence_quality = "Moderate"
        elif rsi_slope > 0.5:
            divergence_points = 2
            divergence_quality = "Slight"
        else:
            divergence_points = 2
            divergence_quality = "Weak"
    else:
        divergence_points = 0
        divergence_quality = "None"
    
    score += divergence_points
    breakdown['rsi_divergence'] = {
        'points': divergence_points,
        'rsi_slope': rsi_slope,
        'price_slope': price_slope,
        'quality': divergence_quality
    }
    
    # RSI in Accumulation Zone (0-2 points)
    rsi = metrics.get('rsi_current', 50)
    in_accumulation_zone = 40 <= rsi <= 65
    accumulation_points = 2 if in_accumulation_zone else 0
    
    score += accumulation_points
    breakdown['rsi_accumulation_zone'] = {
        'points': accumulation_points,
        'rsi': rsi,
        'in_zone': in_accumulation_zone
    }
    
    # MACD Status (0-3 points)
    macd_current = metrics.get('macd_histogram', 0)
    macd_prev = metrics.get('macd_histogram_prev', 0)
    
    if macd_current > 0:
        macd_points = 3
        macd_quality = "Positive"
    elif macd_current > macd_prev and macd_prev < 0:
        macd_points = 2
        macd_quality = "Improving from negative"
    else:
        macd_points = 0
        macd_quality = "Negative/neutral"
    
    score += macd_points
    breakdown['macd_status'] = {
        'points': macd_points,
        'current': macd_current,
        'previous': macd_prev,
        'quality': macd_quality
    }
    
    # OBV Consistency (0-3 points)
    obv_days_rising = metrics.get('obv_days_rising', 0)
    
    if obv_days_rising >= 5:
        obv_points = 3
        obv_quality = "Excellent"
    elif obv_days_rising >= 4:
        obv_points = 2
        obv_quality = "Good"
    elif obv_days_rising >= 3:
        obv_points = 1
        obv_quality = "Moderate"
    else:
        obv_points = 0
        obv_quality = "Weak"
    
    score += obv_points
    breakdown['obv_consistency'] = {
        'points': obv_points,
        'days_rising': obv_days_rising,
        'quality': obv_quality
    }
    
    return {
        'total_score': score,
        'max_score': 12,
        'breakdown': breakdown
    }


def calculate_relative_strength_score(metrics):
    """
    Calculate relative strength score (0-8 points)
    
    Args:
        metrics (dict): Relative strength metrics
            - rs_slope: float
            - outperformance: float (percentage)
    
    Returns:
        dict: {
            'total_score': int (0-8),
            'breakdown': dict with point details
        }
    """
    score = 0
    breakdown = {}
    
    # RS Slope (0-4 points)
    rs_slope = metrics.get('rs_slope', 0)
    
    if rs_slope > 0.005:
        slope_points = 4
        slope_quality = "Strongly positive"
    elif rs_slope > 0.002:
        slope_points = 3
        slope_quality = "Moderately positive"
    elif rs_slope > 0:
        slope_points = 2
        slope_quality = "Slightly positive"
    else:
        slope_points = 0
        slope_quality = "Negative"
    
    score += slope_points
    breakdown['rs_slope'] = {
        'points': slope_points,
        'value': rs_slope,
        'quality': slope_quality
    }
    
    # Outperformance vs SPY (0-4 points)
    outperformance = metrics.get('outperformance', 0)
    
    if outperformance > 5:
        outperf_points = 4
        outperf_quality = "Strong outperformance"
    elif outperformance > 3:
        outperf_points = 3
        outperf_quality = "Solid outperformance"
    elif outperformance > 1:
        outperf_points = 2
        outperf_quality = "Moderate outperformance"
    elif outperformance > 0:
        outperf_points = 1
        outperf_quality = "Slight outperformance"
    else:
        outperf_points = 0
        outperf_quality = "Underperforming"
    
    score += outperf_points
    breakdown['outperformance'] = {
        'points': outperf_points,
        'value': outperformance,
        'quality': outperf_quality
    }
    
    return {
        'total_score': score,
        'max_score': 8,
        'breakdown': breakdown
    }


def calculate_total_score(volume_metrics, momentum_metrics, rs_metrics):
    """
    Calculate total cumulative score from all metrics
    
    Args:
        volume_metrics (dict): Raw volume metrics
        momentum_metrics (dict): Raw momentum metrics
        rs_metrics (dict): Raw relative strength metrics
    
    Returns:
        dict: {
            'total_score': int (0-35),
            'volume_score': dict,
            'momentum_score': dict,
            'rs_score': dict,
            'alert_level': str ('high_priority', 'watch_list', 'skip')
        }
    """
    
    # Calculate individual category scores
    volume_score = calculate_volume_score(volume_metrics)
    momentum_score = calculate_momentum_score(momentum_metrics)
    rs_score = calculate_relative_strength_score(rs_metrics)
    
    # Calculate total
    total = (
        volume_score['total_score'] +
        momentum_score['total_score'] +
        rs_score['total_score']
    )
    
    # Determine alert level
    if total >= 20:
        alert_level = 'high_priority'
        alert_emoji = '✅'
        alert_text = 'STRONG SETUP'
    elif total >= 15:
        alert_level = 'watch_list'
        alert_emoji = '👀'
        alert_text = 'WATCH LIST'
    else:
        alert_level = 'skip'
        alert_emoji = '⏸️'
        alert_text = 'SKIP'
    
    return {
        'total_score': total,
        'max_score': 35,
        'volume_score': volume_score,
        'momentum_score': momentum_score,
        'rs_score': rs_score,
        'alert_level': alert_level,
        'alert_emoji': alert_emoji,
        'alert_text': alert_text
    }


def get_score_summary(score_result):
    """
    Get a human-readable summary of the score
    
    Args:
        score_result (dict): Result from calculate_total_score()
    
    Returns:
        str: Summary text
    """
    total = score_result['total_score']
    max_score = score_result['max_score']
    alert_text = score_result['alert_text']
    
    vol_score = score_result['volume_score']['total_score']
    mom_score = score_result['momentum_score']['total_score']
    rs_score = score_result['rs_score']['total_score']
    
    summary = f"{alert_text} - {total}/{max_score} points\n"
    summary += f"Volume: {vol_score}/15 | Momentum: {mom_score}/12 | RS: {rs_score}/8"
    
    return summary