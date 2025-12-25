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
        
        # Step 1 results
        'step1_signal': step1_result['signal'],
        'step1_score': step1_result['score'],
        'step1_red_volume_ratio': step1_result['details'].get('red_volume_ratio', 0),
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


def run_scanner(limit=None):
    """
    Main scanner function - runs all checks and generates output
    
    Args:
        limit (int): Optional limit on number of tickers to scan
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
    
    # Apply limit if specified
    if limit is not None:
        tickers = tickers[:limit]
        print(f"📊 Limiting scan to first {limit} tickers\n")
    
    print(f"📊 Scanning {len(tickers)} stocks...\n")
    
    # Fetch SPY data once (used for all stocks)
    print("📈 Fetching SPY data for relative strength...")
    spy_df = fetch_spy_data()
    
    if spy_df is None:
        print("❌ Failed to fetch SPY data. Exiting.")
        return
    
    print("✅ SPY data loaded\n")
    
    # Scan all stocks
    results = []
    alert_candidates = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Scanning {ticker}...", end=" ")
        
        result = scan_single_stock(ticker, spy_df)
        
        if result:
            results.append(result)
            
            # Check if meets alert criteria (2 out of 3 signals)
            if result['signals_met'] >= config.ALERT_THRESHOLD:
                alert_candidates.append(result)
                print(f"✅ ALERT! ({result['signals_met']}/3 signals, score: {result['total_score']:.1f})")
            else:
                print(f"({result['signals_met']}/3 signals, score: {result['total_score']:.1f})")
        else:
            print("⚠️  Skipped (insufficient data)")
    
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
    print("\n" + "="*60)
    print("📊 SCAN COMPLETE")
    print("="*60)
    print(f"✅ Stocks Scanned: {len(tickers)}")
    print(f"✅ Results Generated: {len(results)}")
    print(f"🚨 Alerts Triggered: {len(alert_candidates)}")
    print(f"⏱️  Scan Duration: {scan_duration:.1f} seconds")
    print("="*60 + "\n")
    
    # Show top 10 results
    if results:
        print("\n🏆 TOP 10 STOCKS BY SCORE:")
        print("-" * 80)
        print(f"{'Rank':<6}{'Ticker':<10}{'Score':<10}{'Signals':<10}{'Price':<12}{'Details'}")
        print("-" * 80)
        
        for i, stock in enumerate(results[:10], 1):
            signals_str = f"{stock['signals_met']}/3"
            details = []
            if stock['step1_signal']:
                details.append("Vol")
            if stock['step2_signal']:
                details.append("Div")
            if stock['step3_signal']:
                details.append("RS")
            
            details_str = ", ".join(details) if details else "None"
            
            print(f"{i:<6}{stock['ticker']:<10}{stock['total_score']:<10.1f}{signals_str:<10}"
                  f"${stock['current_price']:<11.2f}{details_str}")
        
        print("-" * 80 + "\n")


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
    
    # Reorder columns for better readability - UPDATED with new fields
    column_order = [
        'ticker', 'date', 'signals_met', 'total_score', 'current_price', 'volume',
        'step1_signal', 'step1_score', 'step1_red_volume_ratio', 'step1_price_above_ema',
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
    # Check for command-line arguments
    limit = None
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"\n🎯 Running with limit: {limit} tickers")
        except ValueError:
            print(f"\n⚠️  Invalid limit argument: {sys.argv[1]}")
            print("Usage: python scanner.py [limit]")
            print("Example: python scanner.py 100")
            sys.exit(1)
    
    run_scanner(limit)