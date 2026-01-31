"""
Main Early Breakout Scanner
Orchestrates all signal checks and generates results
"""

import pandas as pd
from datetime import datetime
import time
import os
import config
from data_fetch import load_ticker_list, fetch_stock_data, fetch_spy_data
from volume_dry_up import check_step1
from divergences import check_step2
from relative_strength import check_step3
from discord_alert import send_discord_alert, send_summary_alert
import scoring
import report_generator


def scan_single_stock(ticker, spy_df):
    """
    Run all signal checks on a single stock
    
    Args:
        ticker (str): Stock symbol
        spy_df (pd.DataFrame): SPY data for relative strength
    
    Returns:
        dict: Combined results with scores
    """
    
    # Fetch stock data
    df = fetch_stock_data(ticker)
    
    if df is None or len(df) < 30:
        return None
    
    # Filter out low-volume/illiquid stocks
    avg_volume_20d = df['Volume'].tail(20).mean()
    if avg_volume_20d < 500_000:  # Minimum 500K average daily volume
        return None
    
    # Get raw metrics from signal files
    volume_metrics = check_step1(ticker, df)
    momentum_metrics = check_step2(ticker, df)
    rs_metrics = check_step3(ticker, df, spy_df)
    
    # Calculate score using scoring.py
    score_result = scoring.calculate_total_score(
        volume_metrics,
        momentum_metrics,
        rs_metrics
    )
    
    # Compile results
    result = {
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
        'rs_slope': rs_metrics.get('rs_slope', 0),
        'outperformance': rs_metrics.get('outperformance', 0),
        
        # Price info
        'current_price': df['Close'].iloc[-1],
        'volume': df['Volume'].iloc[-1]
    }
    
    return result


def run_scanner(limit=None, offset=0):
    """
    Main scanner function - runs all checks and generates output
    
    Args:
        limit (int): Optional limit on number of tickers to scan
        offset (int): Starting position in ticker list (for batching)
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
    
    print(f"📊 Scanning {len(tickers)} stocks (offset: {offset})...\n")
    
    # Fetch SPY data once
    print("📈 Fetching SPY data...")
    spy_df = fetch_spy_data()
    
    if spy_df is None:
        print("❌ Failed to fetch SPY data. Exiting.")
        return
    
    print("✅ SPY data loaded\n")
    
    # Scan all stocks
    results = []
    high_priority = []
    watch_list = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Scanning {ticker}...", end=" ")
        
        result = scan_single_stock(ticker, spy_df)
        
        if result:
            results.append(result)
            
            # Categorize by alert level
            if result['alert_level'] == 'high_priority':
                high_priority.append(result)
                print(f"✅ HIGH PRIORITY ({result['total_score']}/35 pts)")
            elif result['alert_level'] == 'watch_list':
                watch_list.append(result)
                print(f"👀 WATCH ({result['total_score']}/35 pts)")
            else:
                print(f"({result['total_score']}/35 pts)")
        else:
            print("⚠️ Skipped")
    
    # Sort results by total score
    results.sort(key=lambda x: x['total_score'], reverse=True)
    high_priority.sort(key=lambda x: x['total_score'], reverse=True)
    watch_list.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Save results to CSV
    save_results(results)
    
    # Generate detailed report for alerted stocks
    if high_priority or watch_list:
        print(f"\n📝 Generating detailed report...")
        report_generator.generate_report(results)
    
    # Send Discord alerts
    alert_count = len(high_priority) + len(watch_list)
    if alert_count > 0:
        print(f"\n🚨 Sending Discord alerts for {alert_count} stocks...")
        send_discord_alert(high_priority + watch_list)
    
    # Calculate scan duration
    scan_duration = time.time() - start_time
    
    # Send summary
    send_summary_alert(len(tickers), alert_count, scan_duration)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 SCAN COMPLETE")
    print("="*60)
    print(f"✅ Stocks Scanned: {len(tickers)}")
    print(f"✅ Results Generated: {len(results)}")
    print(f"🎯 High Priority: {len(high_priority)}")
    print(f"👀 Watch List: {len(watch_list)}")
    print(f"⏱️  Duration: {scan_duration:.1f}s")
    print("="*60 + "\n")
    
    # Show top results
    if high_priority:
        print("\n🎯 HIGH PRIORITY ALERTS:")
        print("-" * 60)
        for stock in high_priority[:10]:  # Top 10
            print(f"{stock['ticker']:<6} ${stock['current_price']:<8.2f} {stock['total_score']}/35 pts")
            print(f"       Vol: {stock['volume_score']}/15 | Mom: {stock['momentum_score']}/12 | RS: {stock['rs_score']}/8")
        print("-" * 60)


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
    df.to_csv(filename, index=False)
    
    print(f"\n💾 Results saved to: {filename}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Early Breakout Scanner')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Number of tickers to scan')
    parser.add_argument('--offset', type=int, default=0,
                       help='Starting position in ticker list')
    parser.add_argument('simple_limit', type=int, nargs='?', default=None,
                       help='Simple limit (legacy syntax)')
    
    args = parser.parse_args()
    
    limit = args.simple_limit if args.simple_limit is not None else args.limit
    offset = args.offset
    
    if limit is not None or offset > 0:
        print(f"\n🎯 Running with offset: {offset}, limit: {limit if limit else 'ALL'}")
    
    run_scanner(limit=limit, offset=offset)