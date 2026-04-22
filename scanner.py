"""
Early Breakout Scanner
Runs all signal checks on a single stock and returns raw metrics
"""

from datetime import datetime
from data_fetch import fetch_stock_data
from volume_dry_up import check_step1
from divergences import check_step2
from relative_strength import check_step3
from compression import check_compression


def scan_single_stock(ticker, spy_df):
    """
    Run all signal checks on a single stock

    Args:
        ticker (str): Stock symbol
        spy_df (pd.DataFrame): SPY data for relative strength

    Returns:
        dict: Combined raw metrics, or None if filtered out
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
    compression_metrics = check_compression(ticker, df)

    return {
        'ticker': ticker,
        'date': datetime.now().strftime('%Y-%m-%d'),

        # Raw metrics - Volume
        'red_volume_ratio': volume_metrics.get('red_volume_ratio', 0),
        'price_above_ema': volume_metrics.get('price_above_ema', False),
        'red_day_avg_volume': volume_metrics.get('red_day_avg_volume', 0),
        'red_day_volume_slope': volume_metrics.get('red_day_volume_slope', 0),
        'red_day_stepdown_count': volume_metrics.get('red_day_stepdown_count', 0),
        'red_day_count': volume_metrics.get('red_day_count', 0),

        # Raw metrics - Momentum
        'rsi_current': momentum_metrics.get('rsi_current', 0),
        'rsi_slope': momentum_metrics.get('rsi_slope', 0),
        'price_slope': momentum_metrics.get('price_slope', 0),
        'macd_histogram': momentum_metrics.get('macd_histogram', 0),
        'macd_histogram_prev': momentum_metrics.get('macd_histogram_prev', 0),
        'obv_days_rising': momentum_metrics.get('obv_days_rising', 0),

        # Raw metrics - Relative Strength
        'outperformance_short': rs_metrics.get('outperformance_short', 0),
        'outperformance_long': rs_metrics.get('outperformance_long', 0),
        'rs_slope_short': rs_metrics.get('rs_slope_short', 0),
        'rs_slope_long': rs_metrics.get('rs_slope_long', 0),

        # Raw metrics - Compression
        'atr_contracting': compression_metrics.get('atr_contracting', False),
        'atr_today': compression_metrics.get('atr_today', None),
        'atr_lookback': compression_metrics.get('atr_lookback', None),
        'near_recent_high': compression_metrics.get('near_recent_high', False),
        'pct_from_high_10d': compression_metrics.get('pct_from_high_10d', None),
        'pct_from_high_20d': compression_metrics.get('pct_from_high_20d', None),
        'pct_from_52w_high': compression_metrics.get('pct_from_52w_high', None),
        'near_52w_high': compression_metrics.get('near_52w_high', False),
        'week_52_high': compression_metrics.get('week_52_high', None),

        # Price info
        'current_price': df['Close'].iloc[-1],
        'volume': df['Volume'].iloc[-1],
    }