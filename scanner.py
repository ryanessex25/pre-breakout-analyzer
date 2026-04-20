"""
Early Breakout Scanner
Runs all signal checks on a single stock and returns scored result
"""

from datetime import datetime
import config
from data_fetch import fetch_stock_data
from volume_dry_up import check_step1
from divergences import check_step2
from relative_strength import check_step3
import scoring


def scan_single_stock(ticker, spy_df):
    """
    Run all signal checks on a single stock

    Args:
        ticker (str): Stock symbol
        spy_df (pd.DataFrame): SPY data for relative strength

    Returns:
        dict: Combined results with scores, or None if filtered out
    """

    df = fetch_stock_data(ticker)

    if df is None or len(df) < 30:
        return None

    avg_volume_20d = df['Volume'].tail(20).mean()
    if avg_volume_20d < 500_000:
        return None

    volume_metrics = check_step1(ticker, df)
    momentum_metrics = check_step2(ticker, df)
    rs_metrics = check_step3(ticker, df, spy_df)

    score_result = scoring.calculate_total_score(
        volume_metrics,
        momentum_metrics,
        rs_metrics
    )

    return {
        'ticker': ticker,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_score': score_result['total_score'],
        'alert_level': score_result['alert_level'],
        'alert_text': score_result['alert_text'],

        # Category scores
        'volume_score': score_result['volume_score']['total_score'],
        'momentum_score': score_result['momentum_score']['total_score'],
        'rs_score': score_result['rs_score']['total_score'],

        # Raw metrics - Volume
        'red_volume_ratio': volume_metrics.get('red_volume_ratio', 0),
        'price_above_ema': volume_metrics.get('price_above_ema', False),
        'red_day_avg_volume': volume_metrics.get('red_day_avg_volume', 0),
        'green_day_avg_volume': volume_metrics.get('green_day_avg_volume', 0),

        # Raw metrics - Momentum
        'rsi_current': momentum_metrics.get('rsi_current', 0),
        'rsi_slope': momentum_metrics.get('rsi_slope', 0),
        'macd_histogram': momentum_metrics.get('macd_histogram', 0),
        'obv_days_rising': momentum_metrics.get('obv_days_rising', 0),

        # Raw metrics - Relative Strength
        'outperformance_short': rs_metrics.get('outperformance_short', 0),
        'outperformance_long': rs_metrics.get('outperformance_long', 0),
        'rs_slope_short': rs_metrics.get('rs_slope_short', 0),
        'rs_slope_long': rs_metrics.get('rs_slope_long', 0),

        # Price info
        'current_price': df['Close'].iloc[-1],
        'volume': df['Volume'].iloc[-1]
    }