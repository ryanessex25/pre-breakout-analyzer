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
        
        # Step 2 results
        'step2_signal': step2_result['signal'],
        'step2_score': step2_result['score'],
        'step2_rsi': step2_result['details'].get('rsi_current', 0),
        'step2_rsi_divergence': step2_result['details'].get('rsi_divergence', False),
        'step2_macd_positive': step2_result['details'].get('macd_turning_positive', False),
        'step2_obv_rising': step2_result['details'].get('obv_rising', False),
        
        # Step 3 results
        'step3_signal': step3_result['signal'],
        'step3_score': step3_result['score'],
        'step3_rs_slope': step3_result['details'].get('rs_slope', 0),
        'step3_outperformance': step3_result['details'].get('outperformance', 0),
        
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
    
    # Step 1: Volume Dry-Up
    s1_icon = "✅" if stock['step1_signal'] else "❌"
    print(f"  {s1_icon} Step 1 - Volume Dry-Up ({stock['step1_score']:.0f}/10)")
    print(f"     • Red day volume: {stock['step1_red_volume_ratio']:.2f}x average " +
          ("(excellent)" if stock['step1_red_volume_ratio'] < 0.5 else 
           "(good)" if stock['step1_red_volume_ratio'] < 0.7 else "(weak)"))
    print(f"     • Price above 21 EMA: {'Yes' if stock['step1_price_above_ema'] else 'No'}")
    
    # Step 2: Divergences
    s2_icon = "✅" if stock['step2_signal'] else "❌"
    print(f"\n  {s2_icon} Step 2 - Divergences ({stock['step2_score']:.0f}/10)")
    print(f"     • RSI: {stock['step2_rsi']:.1f} " +
          ("(divergence detected)" if stock['step2_rsi_divergence'] else "(no divergence)"))
    print(f"     • MACD: {'Turning positive' if stock['step2_macd_positive'] else 'Negative/weak'}")
    print(f"     • OBV: {'Rising' if stock['step2_obv_rising'] else 'Flat/falling'}")
    
    # Step 3: Relative Strength
    s3_icon = "✅" if stock['step3_signal'] else "❌"
    strength_label = ""
    if stock['step3_outperformance'] > 5:
        strength_label = " 🔥 VERY STRONG"
    elif stock['step3_outperformance'] > 2:
        strength_label = " 💪 STRONG"
    elif stock['step3_outperformance'] > 0:
        strength_label = ""
    
    print(f"\n  {s3_icon} Step 3 - Relative Strength ({stock['step3_score']:.0f}/10){strength_label}")
    print(f"     • Outperforming SPY by: {stock['step3_outperformance']:+.1f}%")
    print(f"     • RS slope: {stock['step3_rs_slope']:.6f} " +
          ("(uptrend)" if stock['step3_rs_slope'] > 0 else "(downtrend)"))
    
    print("─" * 80)


def print_alert_results(alert_candidates):
    """
    Enhanced alert display with summary table and detailed breakdown
    
    Args:
        alert_candidates (list): List of stocks meeting alert criteria
    """
    
    if not alert_candidates:
        return
    
    print("\n" + "="*80)
    print("🚨 ALERT STOCKS - Meeting 2+ Signals")
    print("="*80)
    
    # Summary table
    print("\n📊 QUICK SUMMARY:")
    print("-"*80)
    print(f"{'#':<4}{'Ticker':<8}{'Price':<10}{'Score':<8}{'S1':<6}{'S2':<6}{'S3':<6}{'Key Strengths'}")
    print("-"*80)
    
    for i, stock in enumerate(alert_candidates, 1):
        s1 = f"✅{stock['step1_score']:.0f}" if stock['step1_signal'] else f"❌{stock['step1_score']:.0f}"
        s2 = f"✅{stock['step2_score']:.0f}" if stock['step2_signal'] else f"❌{stock['step2_score']:.0f}"
        s3 = f"✅{stock['step3_score']:.0f}" if stock['step3_signal'] else f"❌{stock['step3_score']:.0f}"
        
        strengths = []
        if stock['step1_signal']:
            strengths.append(f"Vol:{stock['step1_red_volume_ratio']:.2f}x")
        if stock['step2_signal']:
            strengths.append(f"RSI:{stock['step2_rsi']:.0f}")
        if stock['step3_signal']:
            strengths.append(f"RS+{stock['step3_outperformance']:.1f}%")
        
        strength_str = ", ".join(strengths[:3])  # Top 3 strengths
        
        print(f"{i:<4}{stock['ticker']:<8}${stock['current_price']:<9.2f}"
              f"{stock['total_score']:<8.0f}{s1:<6}{s2:<6}{s3:<6}{strength_str}")
    
    print("-"*80)
    
    # Detailed breakdown
    print("\n📋 DETAILED BREAKDOWN:")
    print("="*80)
    
    for stock in alert_candidates[:10]:  # Limit to top 10 for detailed view
        print_stock_detail(stock)
    
    if len(alert_candidates) > 10:
        print(f"\n... and {len(alert_candidates) - 10} more stocks")
        print("─" * 80)


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
    
    # Show top 10 all results (including non-alerts)
    if results:
        print("\n" + "="*80)
        print("📈 TOP 10 STOCKS BY SCORE (All Results)")
        print("="*80)
        print(f"{'#':<4}{'Ticker':<8}{'Price':<10}{'Score':<8}{'Sigs':<6}{'S1':<6}{'S2':<6}{'S3':<6}{'Notes'}")
        print("-"*80)
        
        for i, stock in enumerate(results[:10], 1):
            signals_str = f"{stock['signals_met']}/3"
            s1 = f"{stock['step1_score']:.0f}"
            s2 = f"{stock['step2_score']:.0f}"
            s3 = f"{stock['step3_score']:.0f}"
            
            # Build notes
            notes = []
            if stock['step1_signal']:
                notes.append(f"V:{stock['step1_red_volume_ratio']:.2f}x")
            if stock['step3_signal']:
                notes.append(f"RS+{stock['step3_outperformance']:.1f}%")
            notes_str = ", ".join(notes[:2]) if notes else "-"
            
            print(f"{i:<4}{stock['ticker']:<8}${stock['current_price']:<9.2f}"
                  f"{stock['total_score']:<8.0f}{signals_str:<6}{s1:<6}{s2:<6}{s3:<6}{notes_str}")
        
        print("-"*80 + "\n")


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
    
    # Reorder columns for better readability
    column_order = [
        'ticker', 'date', 'signals_met', 'total_score', 'current_price', 'volume',
        'step1_signal', 'step1_score', 'step1_red_volume_ratio', 'step1_price_above_ema',
        'step2_signal', 'step2_score', 'step2_rsi', 'step2_rsi_divergence', 
        'step2_macd_positive', 'step2_obv_rising',
        'step3_signal', 'step3_score', 'step3_rs_slope', 'step3_outperformance'
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