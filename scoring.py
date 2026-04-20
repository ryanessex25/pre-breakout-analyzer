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

def calculate_compression_score(metrics):
    """
    Calculate compression-based score (0-15 points)
    """
    score = 0
    breakdown = {}

    # --- ATR Contracting (0-6 points) ---
    atr_contracting = metrics.get('atr_contracting', False)
    atr_today = metrics.get('atr_today', None)
    atr_lookback = metrics.get('atr_lookback', None)

    if atr_contracting and atr_today and atr_lookback:
        compression_ratio = atr_today / atr_lookback
        if compression_ratio < 0.50:
            atr_points = 6
            atr_quality = "Extreme compression"
        elif compression_ratio < 0.60:
            atr_points = 5
            atr_quality = "Strong compression"
        elif compression_ratio < 0.70:
            atr_points = 4
            atr_quality = "Moderate compression"
        else:
            atr_points = 2
            atr_quality = "Slight compression"
    else:
        atr_points = 0
        atr_quality = "No compression"

    score += atr_points
    breakdown['atr_compression'] = {
        'points': atr_points,
        'contracting': atr_contracting,
        'quality': atr_quality
    }

    # --- 52-Week High Proximity (0-5 points) ---
    pct_from_52w = metrics.get('pct_from_52w_high', 1.0)

    if pct_from_52w is None:
        w52_points = 0
        w52_quality = "No data"
    elif pct_from_52w <= 0.05:
        w52_points = 5
        w52_quality = "Within 5% of 52w high"
    elif pct_from_52w <= 0.10:
        w52_points = 4
        w52_quality = "Within 10% of 52w high"
    elif pct_from_52w <= 0.15:
        w52_points = 3
        w52_quality = "Within 15% of 52w high"
    elif pct_from_52w <= 0.20:
        w52_points = 1
        w52_quality = "Within 20% of 52w high"
    else:
        w52_points = 0
        w52_quality = "Far from 52w high"

    score += w52_points
    breakdown['week_52_proximity'] = {
        'points': w52_points,
        'pct_from_52w_high': pct_from_52w,
        'quality': w52_quality
    }

    # --- Near Recent High (0-4 points) ---
    near_recent_high = metrics.get('near_recent_high', False)
    pct_from_high_10d = metrics.get('pct_from_high_10d', None)
    pct_from_high_20d = metrics.get('pct_from_high_20d', None)

    if near_recent_high:
        # Both timeframes near high is stronger than just one
        pct_10d_near = pct_from_high_10d is not None and pct_from_high_10d <= 0.03
        pct_20d_near = pct_from_high_20d is not None and pct_from_high_20d <= 0.03

        if pct_10d_near and pct_20d_near:
            near_points = 4
            near_quality = "Near both 10d and 20d highs"
        else:
            near_points = 2
            near_quality = "Near one recent high"
    else:
        near_points = 0
        near_quality = "Not near recent high"

    score += near_points
    breakdown['near_recent_high'] = {
        'points': near_points,
        'near_high': near_recent_high,
        'quality': near_quality
    }

    return {
        'total_score': score,
        'max_score': 15,
        'breakdown': breakdown
    }

def calculate_relative_strength_score(metrics):
    score = 0
    breakdown = {}

    # --- Long-term RS Slope (0-2 points) ---
    rs_slope_long = metrics.get('rs_slope_long', 0)

    if rs_slope_long > 0.005:
        long_slope_points = 2
        long_slope_quality = "Strongly positive"
    elif rs_slope_long > 0.002:
        long_slope_points = 1
        long_slope_quality = "Moderately positive"
    else:
        long_slope_points = 0
        long_slope_quality = "Flat or negative"

    score += long_slope_points
    breakdown['rs_slope_long'] = {
        'points': long_slope_points,
        'value': rs_slope_long,
        'quality': long_slope_quality
    }

    # --- Long-term Outperformance vs SPY (0-2 points) ---
    outperformance_long = metrics.get('outperformance_long', 0)

    if outperformance_long > 10:
        long_outperf_points = 2
        long_outperf_quality = "Strong 3-month outperformance"
    elif outperformance_long > 5:
        long_outperf_points = 1
        long_outperf_quality = "Moderate 3-month outperformance"
    else:
        long_outperf_points = 0
        long_outperf_quality = "Underperforming or flat"

    score += long_outperf_points
    breakdown['outperformance_long'] = {
        'points': long_outperf_points,
        'value': outperformance_long,
        'quality': long_outperf_quality
    }

    # --- Short-term RS Slope (0-2 points) ---
    rs_slope_short = metrics.get('rs_slope_short', 0)

    if rs_slope_short > 0.005:
        short_slope_points = 2
        short_slope_quality = "Strongly positive"
    elif rs_slope_short > 0.002:
        short_slope_points = 1
        short_slope_quality = "Moderately positive"
    else:
        short_slope_points = 0
        short_slope_quality = "Flat or negative"

    score += short_slope_points
    breakdown['rs_slope_short'] = {
        'points': short_slope_points,
        'value': rs_slope_short,
        'quality': short_slope_quality
    }

    # --- Short-term Outperformance vs SPY (0-2 points) ---
    outperformance_short = metrics.get('outperformance_short', 0)

    if outperformance_short > 5:
        short_outperf_points = 2
        short_outperf_quality = "Strong 2-week outperformance"
    elif outperformance_short > 2:
        short_outperf_points = 1
        short_outperf_quality = "Moderate 2-week outperformance"
    else:
        short_outperf_points = 0
        short_outperf_quality = "Underperforming or flat"

    score += short_outperf_points
    breakdown['outperformance_short'] = {
        'points': short_outperf_points,
        'value': outperformance_short,
        'quality': short_outperf_quality
    }

    return {
        'total_score': score,
        'max_score': 8,
        'breakdown': breakdown
    }

def calculate_total_score(volume_metrics, momentum_metrics, rs_metrics, compression_metrics):
    
    volume_score = calculate_volume_score(volume_metrics)
    momentum_score = calculate_momentum_score(momentum_metrics)
    rs_score = calculate_relative_strength_score(rs_metrics)
    compression_score = calculate_compression_score(compression_metrics)

    total = (
        volume_score['total_score'] +
        momentum_score['total_score'] +
        rs_score['total_score'] +
        compression_score['total_score']
    )

    if total >= 30:
        alert_level = 'high_priority'
        alert_emoji = '✅'
        alert_text = 'STRONG SETUP'
    elif total >= 22:
        alert_level = 'watch_list'
        alert_emoji = '👀'
        alert_text = 'WATCH LIST'
    else:
        alert_level = 'skip'
        alert_emoji = '⏸️'
        alert_text = 'SKIP'

    return {
        'total_score': total,
        'max_score': 50,
        'volume_score': volume_score,
        'momentum_score': momentum_score,
        'rs_score': rs_score,
        'compression_score': compression_score,
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