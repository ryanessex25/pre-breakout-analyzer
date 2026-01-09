"""
Backtesting tool for Early Breakout Scanner
Tests scanner against known breakouts to validate signal quality
"""

import pandas as pd
from datetime import datetime, timedelta
import config
from data_fetch import fetch_stock_data, fetch_spy_data
from volume_dry_up import check_step1
from divergences import check_step2
from relative_strength import check_step3


# ===== TEST CASES =====
# Known breakouts from 2025 to validate against
TEST_CASES = [
    {
        'ticker': 'CVNA',
        'name': 'Carvana',
        'breakout_start': '2025-11-21',
        'breakout_end': '2025-12-11',
        'start_price': 309,
        'peak_price': 472,
        'notes': 'Strong breakout, 52.8% gain in 3 weeks'
    },
    {
        'ticker': 'TSLA',
        'name': 'Tesla',
        'breakout_start': '2025-11-20',
        'breakout_end': '2025-12-17',
        'start_price': 390,
        'peak_price': 490,
        'notes': 'Steady climb, 25.6% gain'
    },
    {
        'ticker': 'ASTS',
        'name': 'AST SpaceMobile',
        'breakout_start': '2025-11-21',
        'breakout_end': '2025-12-11',
        'start_price': 51,
        'peak_price': 85,
        'notes': 'Explosive move, 66.7% gain in 3 weeks'
    },
    {
        'ticker': 'SNDK',
        'name': 'SanDisk',
        'breakout_start': '2025-11-20',
        'breakout_end': '2025-12-20',
        'start_price': 200,
        'peak_price': 360,
        'notes': 'Consolidation around $200, then 80% breakout'
    }
]


def generate_scan_dates(breakout_date_str):
    """
    Generate scan dates leading up to breakout
    
    Args:
        breakout_date_str (str): Breakout date in 'YYYY-MM-DD' format
    
    Returns:
        list: List of date strings to scan
    """
    breakout_date = datetime.strptime(breakout_date_str, '%Y-%m-%d')
    
    scan_dates = [
        breakout_date - timedelta(days=14),  # 2 weeks before
        breakout_date - timedelta(days=10),  # 10 days before
        breakout_date - timedelta(days=7),   # 1 week before
        breakout_date - timedelta(days=3),   # 3 days before
        breakout_date                        # Day of breakout
    ]
    
    return [d.strftime('%Y-%m-%d') for d in scan_dates]


def run_scanner_on_date(ticker, as_of_date, spy_df):
    """
    Run scanner on a specific stock as of a historical date
    
    Args:
        ticker (str): Stock symbol
        as_of_date (str): Date to run scanner (YYYY-MM-DD)
        spy_df (pd.DataFrame): Full SPY historical data
    
    Returns:
        dict: Scanner results or None if insufficient data
    """
    # Fetch stock data up to this date
    df = fetch_stock_data(ticker, days=90)
    
    if df is None or len(df) < 30:
        return None
    
    # Filter data to only include dates up to as_of_date
    cutoff_date = pd.to_datetime(as_of_date)
    df = df[df.index <= cutoff_date]
    
    if len(df) < 30:
        return None
    
    # Filter SPY data similarly
    spy_filtered = spy_df[spy_df.index <= cutoff_date]
    
    if len(spy_filtered) < 30:
        return None
    
    # Run all three signal checks
    step1_result = check_step1(ticker, df)
    step2_result = check_step2(ticker, df)
    step3_result = check_step3(ticker, df, spy_filtered)
    
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
    
    # Get current price as of this date
    current_price = df['Close'].iloc[-1]
    
    return {
        'date': as_of_date,
        'ticker': ticker,
        'signals_met': signals_met,
        'total_score': total_score,
        'current_price': current_price,
        'alert_triggered': signals_met >= config.ALERT_THRESHOLD,
        
        # Step 1 details
        'step1_signal': step1_result['signal'],
        'step1_score': step1_result['score'],
        'step1_details': step1_result['details'],
        
        # Step 2 details
        'step2_signal': step2_result['signal'],
        'step2_score': step2_result['score'],
        'step2_details': step2_result['details'],
        
        # Step 3 details
        'step3_signal': step3_result['signal'],
        'step3_score': step3_result['score'],
        'step3_details': step3_result['details']
    }


def print_result_summary(result, breakout_date, days_before):
    """
    Print formatted summary of a single scan result
    
    Args:
        result (dict): Scanner result
        breakout_date (str): Date of breakout
        days_before (int): Days before breakout
    """
    if result is None:
        print(f"  ⚠️  Insufficient data")
        return
    
    # Alert status
    if result['alert_triggered']:
        status = "🚨 ALERT!"
        status_color = "✅"
    else:
        status = "No Alert"
        status_color = "❌"
    
    print(f"\n{result['date']}: {status_color} {status} ({result['signals_met']}/3 signals) - Score: {result['total_score']:.0f}/30")
    print(f"  Price: ${result['current_price']:.2f}")
    
    if days_before > 0:
        print(f"  → {days_before} days before breakout")
    elif days_before == 0:
        print(f"  → Breakout day")
    
    # Signal breakdown
    signals = []
    
    if result['step1_signal']:
        signals.append(f"✅ Volume Dry-Up ({result['step1_score']} pts)")
    else:
        signals.append(f"❌ Volume Dry-Up ({result['step1_score']} pts)")
    
    if result['step2_signal']:
        signals.append(f"✅ Divergences ({result['step2_score']} pts)")
    else:
        signals.append(f"❌ Divergences ({result['step2_score']} pts)")
    
    if result['step3_signal']:
        signals.append(f"✅ Rel. Strength ({result['step3_score']} pts)")
    else:
        signals.append(f"❌ Rel. Strength ({result['step3_score']} pts)")
    
    for signal in signals:
        print(f"  {signal}")


def backtest_single_stock(test_case):
    """
    Backtest scanner on a single known breakout
    
    Args:
        test_case (dict): Test case definition
    
    Returns:
        dict: Backtest results
    """
    ticker = test_case['ticker']
    name = test_case['name']
    breakout_start = test_case['breakout_start']
    breakout_end = test_case['breakout_end']
    start_price = test_case['start_price']
    peak_price = test_case['peak_price']
    
    gain_pct = ((peak_price - start_price) / start_price) * 100
    
    print("\n" + "="*80)
    print(f"🔍 BACKTESTING: {ticker} - {name}")
    print("="*80)
    print(f"Breakout: {breakout_start} → {breakout_end}")
    print(f"Price Move: ${start_price:.2f} → ${peak_price:.2f} (+{gain_pct:.1f}%)")
    print(f"Notes: {test_case.get('notes', 'N/A')}")
    print("-"*80)
    
    # Generate scan dates
    scan_dates = generate_scan_dates(breakout_start)
    
    print(f"\nScanning on {len(scan_dates)} dates leading up to breakout...")
    
    # Fetch SPY data once
    spy_df = fetch_spy_data(days=120)
    
    if spy_df is None:
        print("❌ Failed to fetch SPY data. Cannot proceed.")
        return None
    
    # Run scanner on each date
    results = []
    breakout_date = datetime.strptime(breakout_start, '%Y-%m-%d')
    
    for scan_date in scan_dates:
        scan_date_obj = datetime.strptime(scan_date, '%Y-%m-%d')
        days_before = (breakout_date - scan_date_obj).days
        
        result = run_scanner_on_date(ticker, scan_date, spy_df)
        
        if result:
            results.append(result)
            print_result_summary(result, breakout_start, days_before)
    
    # Summary
    print("\n" + "-"*80)
    print("📊 SUMMARY:")
    
    alerts = [r for r in results if r['alert_triggered']]
    
    if alerts:
        earliest_alert = alerts[0]
        earliest_date = datetime.strptime(earliest_alert['date'], '%Y-%m-%d')
        days_early = (breakout_date - earliest_date).days
        
        print(f"✅ Scanner caught this breakout!")
        print(f"   First alert: {earliest_alert['date']} ({days_early} days before breakout)")
        print(f"   Entry price: ${earliest_alert['current_price']:.2f}")
        print(f"   Peak price: ${peak_price:.2f}")
        
        entry_to_peak_gain = ((peak_price - earliest_alert['current_price']) / earliest_alert['current_price']) * 100
        print(f"   Potential gain: +{entry_to_peak_gain:.1f}%")
        
        # Which signals triggered
        triggered_signals = []
        if earliest_alert['step1_signal']:
            triggered_signals.append("Volume Dry-Up")
        if earliest_alert['step2_signal']:
            triggered_signals.append("Divergences")
        if earliest_alert['step3_signal']:
            triggered_signals.append("Rel. Strength")
        
        print(f"   Winning combo: {', '.join(triggered_signals)}")
    else:
        print(f"❌ Scanner did NOT catch this breakout")
        print(f"   Highest score: {max([r['total_score'] for r in results]):.0f}/30")
        print(f"   Most signals: {max([r['signals_met'] for r in results])}/3")
    
    print("="*80 + "\n")
    
    return {
        'ticker': ticker,
        'name': name,
        'caught': len(alerts) > 0,
        'days_early': (breakout_date - datetime.strptime(alerts[0]['date'], '%Y-%m-%d')).days if alerts else None,
        'results': results
    }


def run_full_backtest():
    """
    Run backtest on all test cases
    """
    print("\n" + "="*80)
    print("🚀 EARLY BREAKOUT SCANNER - PHASE 1 BACKTEST")
    print("="*80)
    print(f"Testing against {len(TEST_CASES)} known breakouts from 2025")
    print("="*80 + "\n")
    
    all_results = []
    
    for test_case in TEST_CASES:
        result = backtest_single_stock(test_case)
        if result:
            all_results.append(result)
    
    # Overall summary
    print("\n" + "="*80)
    print("📈 OVERALL BACKTEST RESULTS")
    print("="*80)
    
    caught_count = sum(1 for r in all_results if r['caught'])
    total_count = len(all_results)
    catch_rate = (caught_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n✅ Breakouts Caught: {caught_count}/{total_count} ({catch_rate:.1f}%)")
    
    if caught_count > 0:
        avg_days_early = sum(r['days_early'] for r in all_results if r['caught']) / caught_count
        print(f"📅 Average Detection: {avg_days_early:.1f} days before breakout")
    
    print("\n" + "-"*80)
    print("Stock-by-Stock:")
    for result in all_results:
        status = "✅" if result['caught'] else "❌"
        days_str = f"({result['days_early']}d early)" if result['caught'] else "(missed)"
        print(f"  {status} {result['ticker']:<8} {days_str:<15} {result['name']}")
    
    print("="*80 + "\n")
    
    # Save detailed results
    save_backtest_results(all_results)


def save_backtest_results(results):
    """
    Save detailed backtest results to CSV
    
    Args:
        results (list): List of backtest results
    """
    rows = []
    
    for stock_result in results:
        for scan_result in stock_result['results']:
            rows.append({
                'ticker': stock_result['ticker'],
                'stock_name': stock_result['name'],
                'scan_date': scan_result['date'],
                'signals_met': scan_result['signals_met'],
                'total_score': scan_result['total_score'],
                'alert_triggered': scan_result['alert_triggered'],
                'price': scan_result['current_price'],
                
                'step1_signal': scan_result['step1_signal'],
                'step1_score': scan_result['step1_score'],
                
                'step2_signal': scan_result['step2_signal'],
                'step2_score': scan_result['step2_score'],
                
                'step3_signal': scan_result['step3_signal'],
                'step3_score': scan_result['step3_score'],
                
                'caught_breakout': stock_result['caught'],
                'days_early': stock_result['days_early']
            })
    
    df = pd.DataFrame(rows)
    
    filename = f"results/backtest_results_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"💾 Detailed results saved to: {filename}\n")


if __name__ == "__main__":
    run_full_backtest()