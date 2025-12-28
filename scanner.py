"""
Main Early Breakout Scanner
Orchestrates all signal checks and generates results
"""

import pandas as pd
from datetime import datetime
import time
import os
import sys
import config
from data_fetch import load_ticker_list, fetch_stock_data, fetch_spy_data
from volume_dry_up import check_step1
from divergences import check_step2
from relative_strength import check_step3
from discord_alert import send_discord_alert, send_summary_alert


def scan_single_stock(ticker, spy_df):
    """
    Run all signal checks on a single stock
    
    Args:
        ticker (str): Stock symbol
        spy_df (pd.DataFrame): SPY data for relative strength
    
    Returns:
        dict: Combined results from all signals
    """
    
    # Fetch stock data
    df = fetch_stock_data(ticker)
    
    if df is None or len(df) < 30:
        return None
    
    # Run all three signal checks
    step1_result = check_step1(ticker, df)
    step2_result = check_step2(ticker, df)
    step3_result = check_step3(ticker, df, spy_df)
    
    # Count signals met
    signals_met = sum([
        step1_result['signal'],
        step2_result['signal'],
        step3_result['signal']
    ])
    
    # Calculate total score
    total_score = (
        step1_result['score'] +
        step2_result['score'] +
        step3_result['score']
    )
    
    # Compile results
    result = {
        'ticker': ticker,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'signals_met': signals_met,
        'total_score': total_score,
        
        # Step 1 results - UPDATED with detailed volume breakdown
        'step1_signal': step1_result['signal'],
        'step1_score': step1_result['score'],
        'step1_red_volume_ratio': step1_result['details'].get('red_volume_ratio', 0),
        'step1_red_day_avg_volume': step1_result['details'].get('red_day_avg_volume', 0),
        'step1_green_day_avg_volume': step1_result['details'].get('green_day_avg_volume', 0),
        'step1_20d_avg_volume': step1_result['details'].get('20d_avg_volume', 0),
        'step1_red_day_count': step1_result['details'].get('red_day_count', 0),
        'step1_green_day_count': step1_result['details'].get('green_day_count', 0),
        'step1_price_above_ema': step1_result['details'].get('price_above_ema_21', False),
        
        # Step 2 results - UPDATED with new MACD fields
        'step2_signal': step2_result['signal'],
        'step2_score': step2_result['score'],
        'step2_rsi': step2_result['details'].get('rsi_current', 0),
        'step2_rsi_divergence': step2_result['details'].get('rsi_divergence', False),
        'step2_rsi_in_accumulation_zone': step2_result['details'].get('rsi_in_accumulation_zone', False),
        'step2_macd_histogram': step2_result['details'].get('macd_histogram', 0),
        'step2_macd_histogram_prev': step2_result['details'].get('macd_histogram_prev', 0),
        'step2_macd_improving_from_negative': step2_result['details'].get('macd_improving_from_negative', False),
        'step2_macd_histogram_positive': step2_result['details'].get('macd_histogram_positive', False),
        'step2_macd_turning_positive': step2_result['details'].get('macd_turning_positive', False),
        'step2_obv_rising': step2_result['details'].get('obv_rising', False),
        
        # Step 3 results - UPDATED with new RS fields
        'step3_signal': step3_result['signal'],
        'step3_score': step3_result['score'],
        'step3_rs_slope': step3_result['details'].get('rs_slope', 0),
        'step3_rs_slope_recent': step3_result['details'].get('rs_slope_recent', 0),
        'step3_rs_just_turned_positive': step3_result['details'].get('rs_just_turned_positive', False),
        'step3_outperformance': step3_result['details'].get('outperformance', 0),
        'step3_stock_change_20d': step3_result['details'].get('stock_change_20d', 0),
        
        # Price info
        'current_price': df['Close'].iloc[-1],
        'volume': df['Volume'].iloc[-1]
    }
    
    return result


def print_stock_detail(stock):
    """
    Print detailed breakdown for a single alerted stock
    
    Args:
        stock (dict): Stock result dictionary
    """
    
    print(f"\n📈 {stock['ticker']} - ${stock['current_price']:.2f} | Score: {stock['total_score']:.0f}/30 | {stock['signals_met']}/3 Signals")
    print("─" * 80)
    
    # Step 1: Volume Dry-Up - ENHANCED with detailed breakdown
    print(f"  Step 1 - Volume Dry-Up ({stock['step1_score']:.0f}/10)")
    
    # Get volume details from step1 results
    red_vol_ratio = stock['step1_red_volume_ratio']
    red_day_avg = stock.get('step1_red_day_avg_volume', 0)
    green_day_avg = stock.get('step1_green_day_avg_volume', 0)
    overall_avg = stock.get('step1_20d_avg_volume', 0)
    red_count = stock.get('step1_red_day_count', 0)
    green_count = stock.get('step1_green_day_count', 0)
    
    # Determine quality rating
    if red_vol_ratio < 0.5:
        quality = "Excellent - Strong dry-up!"
        quality_range = "0.20-0.49x: Red days have 20-49% of average volume"
    elif red_vol_ratio < 0.7:
        quality = "Good - Decent dry-up"
        quality_range = "0.50-0.69x: Red days have 50-69% of average volume"
    elif red_vol_ratio < 0.9:
        quality = "Okay - Some dry-up"
        quality_range = "0.70-0.89x: Red days have 70-89% of average volume"
    elif red_vol_ratio <= 1.1:
        quality = "Weak - No real dry-up"
        quality_range = "0.90-1.10x: Red days equal average volume"
    else:
        quality = "Bad - Heavy selling on red days"
        quality_range = ">1.10x: Red days have MORE volume than average"
    
    print(f"     • Red volume ratio: {red_vol_ratio:.2f}x")
    print(f"     • Quality: {quality}")
    print(f"     • Interpretation: {quality_range}")
    if overall_avg > 0:
        print(f"     • Overall 20-day average volume: {overall_avg:,.0f} shares/day")
    if red_count > 0:
        print(f"     • Red days ({red_count} days): Average volume = {red_day_avg:,.0f} shares")
    if green_count > 0:
        print(f"     • Green days ({green_count} days): Average volume = {green_day_avg:,.0f} shares")
    print(f"     • Price above 21 EMA: {'Yes' if stock['step1_price_above_ema'] else 'No'}")
    print(f"     • Signal triggered: {'Yes' if stock['step1_signal'] else 'No'}")
    
    # Step 2: Divergences - Show ALL fields
    print(f"\n  Step 2 - Divergences ({stock['step2_score']:.0f}/10)")
    print(f"     • RSI: {stock['step2_rsi']:.1f}")
    print(f"     • RSI in accumulation zone (40-65): {'Yes' if stock.get('step2_rsi_in_accumulation_zone', False) else 'No'}")
    print(f"     • RSI divergence detected: {'Yes' if stock['step2_rsi_divergence'] else 'No'}")
    
    # MACD - show all values
    macd_hist = stock.get('step2_macd_histogram', 0)
    macd_prev = stock.get('step2_macd_histogram_prev', 0)
    macd_improving = stock.get('step2_macd_improving_from_negative', False)
    macd_positive = stock.get('step2_macd_histogram_positive', False)
    
    print(f"     • MACD histogram (current): {macd_hist:.4f}")
    print(f"     • MACD histogram (previous): {macd_prev:.4f}")
    print(f"     • MACD improving from negative: {'Yes' if macd_improving else 'No'}")
    print(f"     • MACD histogram positive: {'Yes' if macd_positive else 'No'}")
    print(f"     • OBV rising: {'Yes' if stock['step2_obv_rising'] else 'No'}")
    print(f"     • Signal triggered: {'Yes' if stock['step2_signal'] else 'No'}")
    
    # Step 3: Relative Strength - Show ALL fields
    print(f"\n  Step 3 - Relative Strength ({stock['step3_score']:.0f}/10)")
    print(f"     • Outperformance vs SPY: {stock['step3_outperformance']:+.1f}%")
    print(f"     • RS slope (5-day): {stock['step3_rs_slope']:.6f}")
    print(f"     • RS slope (3-day recent): {stock.get('step3_rs_slope_recent', 0):.6f}")
    print(f"     • RS just turned positive: {'Yes' if stock.get('step3_rs_just_turned_positive', False) else 'No'}")
    print(f"     • Stock 20-day move: {stock.get('step3_stock_change_20d', 0):+.1f}%")
    print(f"     • Signal triggered: {'Yes' if stock['step3_signal'] else 'No'}")
    
    print("─" * 80)


def print_alert_results(alert_candidates):
    """
    Print detailed breakdown for ALL alerted stocks
    
    Args:
        alert_candidates (list): List of stocks meeting alert criteria
    """
    
    if not alert_candidates:
        return
    
    print("\n" + "="*80)
    print("🚨 ALERT STOCKS - Meeting 2+ Signals")
    print("="*80)
    
    # Detailed breakdown for ALL stocks
    print(f"\n📋 DETAILED BREAKDOWN ({len(alert_candidates)} stocks):")
    print("="*80)
    
    for stock in alert_candidates:  # Show ALL stocks, not just top 10
        print_stock_detail(stock)


def run_scanner(limit=None, offset=0):
    """
    Main scanner function - runs all checks and generates output
    
    Args:
        limit (int): Optional limit on number of tickers to scan
        offset (int): Starting position in ticker list (for batching large scans)
    """
    
    print("\n" + "="*60)
    print("🔍 EARLY BREAKOUT SCANNER - Starting Scan")
    print("="*60 + "\n")
    
    start_time = time.time()
    
    # Load ticker list
    tickers = load_ticker_list()
    
    if not tickers:
        print("❌ No tickers to scan. Exiting.")
        return
    
    # Apply offset and limit
    total_tickers = len(tickers)
    
    if offset >= total_tickers:
        print(f"❌ Offset {offset} exceeds total tickers ({total_tickers}). Exiting.")
        return
    
    tickers = tickers[offset:]
    
    if limit is not None:
        tickers = tickers[:limit]
    
    print(f"📊 Total tickers available: {total_tickers}")
    print(f"📊 Starting at position: {offset}")
    print(f"📊 Scanning {len(tickers)} stocks (positions {offset} to {offset + len(tickers) - 1})...\n")
    
    
    # Fetch SPY data once (used for all stocks)
    print("📈 Fetching SPY data for relative strength...")
    spy_df = fetch_spy_data()
    
    if spy_df is None:
        print("❌ Failed to fetch SPY data. Exiting.")
        return
    
    print("✅ SPY data loaded\n")
    
    # Scan all stocks with progress bar
    results = []
    alert_candidates = []
    skipped_count = 0
    
    print("Progress:")
    for i, ticker in enumerate(tickers, 1):
        # Calculate progress
        progress = i / len(tickers)
        bar_length = 50
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Update progress bar (overwrite same line)
        print(f'\r[{bar}] {i}/{len(tickers)} ({progress*100:.1f}%) - Current: {ticker:<6} | Alerts: {len(alert_candidates)} | Skipped: {skipped_count}', end='', flush=True)
        
        result = scan_single_stock(ticker, spy_df)
        
        if result:
            results.append(result)
            
            # Check if meets alert criteria (2 out of 3 signals)
            if result['signals_met'] >= config.ALERT_THRESHOLD:
                alert_candidates.append(result)
        else:
            skipped_count += 1
    
    # Print newline after progress bar completes
    print()  # Move to next line after progress bar
    
    # Sort results by total score
    results.sort(key=lambda x: x['total_score'], reverse=True)
    alert_candidates.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Save results to CSV
    save_results(results)
    
    # Send Discord alerts
    if alert_candidates:
        print(f"\n🚨 Sending Discord alerts for {len(alert_candidates)} stocks...")
        send_discord_alert(alert_candidates)
    
    # Calculate scan duration
    scan_duration = time.time() - start_time
    
    # Send summary
    send_summary_alert(len(tickers), len(alert_candidates), scan_duration)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 SCAN COMPLETE")
    print("="*80)
    print(f"✅ Stocks Scanned: {len(tickers)}")
    print(f"✅ Results Generated: {len(results)}")
    print(f"🚨 Alerts Triggered: {len(alert_candidates)}")
    print(f"⏱️  Scan Duration: {scan_duration:.1f} seconds")
    print("="*80 + "\n")
    
    # Show alert results with enhanced display
    if alert_candidates:
        print_alert_results(alert_candidates)


def save_results(results):
    """
    Save scan results to CSV file
    
    Args:
        results (list): List of scan results
    """
    
    if not results:
        print("⚠️  No results to save")
        return
    
    # Create results directory if it doesn't exist
    os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
    
    # Create filename with today's date
    filename = f"{config.RESULTS_FOLDER}/scan_results_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    # Convert to DataFrame and save
    df = pd.DataFrame(results)
    
    # Reorder columns for better readability - UPDATED with all new fields
    column_order = [
        'ticker', 'date', 'signals_met', 'total_score', 'current_price', 'volume',
        'step1_signal', 'step1_score', 'step1_red_volume_ratio', 
        'step1_red_day_avg_volume', 'step1_green_day_avg_volume', 'step1_20d_avg_volume',
        'step1_red_day_count', 'step1_green_day_count', 'step1_price_above_ema',
        'step2_signal', 'step2_score', 'step2_rsi', 'step2_rsi_divergence', 
        'step2_rsi_in_accumulation_zone',
        'step2_macd_histogram', 'step2_macd_histogram_prev',
        'step2_macd_improving_from_negative', 'step2_macd_histogram_positive',
        'step2_macd_turning_positive', 'step2_obv_rising',
        'step3_signal', 'step3_score', 'step3_rs_slope', 'step3_rs_slope_recent',
        'step3_rs_just_turned_positive', 'step3_outperformance', 'step3_stock_change_20d'
    ]
    
    df = df[column_order]
    df.to_csv(filename, index=False)
    
    print(f"\n💾 Results saved to: {filename}")


if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Early Breakout Scanner')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Number of tickers to scan')
    parser.add_argument('--offset', type=int, default=0,
                       help='Starting position in ticker list (for batching)')
    
    # For backward compatibility, also accept a single positional argument
    parser.add_argument('simple_limit', type=int, nargs='?', default=None,
                       help='Simple limit (legacy syntax)')
    
    args = parser.parse_args()
    
    # Determine limit and offset
    limit = args.simple_limit if args.simple_limit is not None else args.limit
    offset = args.offset
    
    if limit is not None or offset > 0:
        print(f"\n🎯 Running with offset: {offset}, limit: {limit if limit else 'ALL'}")
    
    run_scanner(limit=limit, offset=offset)