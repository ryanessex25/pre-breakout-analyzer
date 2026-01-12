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
# Known breakouts from 2025-2026 to validate against
# Currently focused on SLV - silver breakout
TEST_CASES = [
    {
        'ticker': 'SLV',
        'name': 'iShares Silver Trust',
        'breakout_start': '2025-12-01',   # Broke out in December
        'breakout_end': '2025-12-20',     # Reached mid-70s
        'start_price': 49,                # Top of consolidation range
        'peak_price': 75,                 # Peak in mid-70s
        'notes': 'Consolidation: mid-Oct to end-Nov 2025 range $42-$49, broke out Dec, reached mid-70s (+53%)'
    }
]


def generate_scan_dates(breakout_date_str):
    """
    Generate DAILY scan dates for comprehensive analysis
    
    Strategy: Scan every single day for 60 days leading up to breakout
    This shows exactly when signals first appeared during consolidation
    
    Args:
        breakout_date_str (str): Breakout date in 'YYYY-MM-DD' format
    
    Returns:
        list: List of date strings to scan (60 days before through breakout)
    """
    breakout_date = datetime.strptime(breakout_date_str, '%Y-%m-%d')
    
    # Generate daily scan dates from 60 days before through breakout day
    scan_dates = []
    
    for days_back in range(60, -1, -1):  # 60, 59, 58, ... 1, 0
        scan_dates.append(breakout_date - timedelta(days=days_back))
    
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
    
    if df is None:
        print(f"    ❌ fetch_stock_data returned None for {ticker} on {as_of_date}")
        return None
    
    print(f"    📊 {as_of_date}: Fetched {len(df)} rows, range: {df.index[0].date()} to {df.index[-1].date()}")
    
    if len(df) < 30:
        print(f"    ⚠️  Initial data insufficient ({len(df)} < 30)")
        return None
    
    # Ensure timezone-naive for filtering
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    # Filter data to only include dates up to as_of_date
    cutoff_date = pd.to_datetime(as_of_date).normalize()  # Remove time component
    df = df[df.index.normalize() <= cutoff_date]
    
    print(f"    ✂️  After cutoff filter: {len(df)} rows remaining")
    
    if len(df) < 30:
        print(f"    ❌ Post-filter insufficient ({len(df)} < 30 rows)")
        return None
    
    # Filter SPY data similarly (ensure timezone-naive)
    if spy_df.index.tz is not None:
        spy_filtered = spy_df.copy()
        spy_filtered.index = spy_filtered.index.tz_localize(None)
    else:
        spy_filtered = spy_df.copy()
    
    cutoff_date = pd.to_datetime(as_of_date).normalize()
    spy_filtered = spy_filtered[spy_filtered.index.normalize() <= cutoff_date]
    
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


def print_result_summary(result, breakout_date, days_diff, days_label):
    """
    Print formatted summary of a single scan result
    
    Args:
        result (dict): Scanner result
        breakout_date (str): Date of breakout
        days_diff (int): Days relative to breakout (negative = before, positive = after)
        days_label (str): Human-readable label for timing
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
    print(f"  → {days_label}")
    
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
    
    print(f"\nScanning EVERY DAY for 60 days leading up to breakout ({len(scan_dates)} dates)...")
    print("Strategy: Daily granularity to pinpoint exactly when signals appeared\n")
    
    # Fetch SPY data once
    spy_df = fetch_spy_data(days=120)
    
    if spy_df is None:
        print("❌ Failed to fetch SPY data. Cannot proceed.")
        return None
    
    # Run scanner on each date
    results = []
    breakout_date = datetime.strptime(breakout_start, '%Y-%m-%d')
    
    failed_dates = 0
    
    for scan_date in scan_dates:
        scan_date_obj = datetime.strptime(scan_date, '%Y-%m-%d')
        days_diff = (scan_date_obj - breakout_date).days
        
        if days_diff < 0:
            days_label = f"{abs(days_diff)} days before breakout"
        elif days_diff == 0:
            days_label = "Breakout day"
        else:
            days_label = f"{days_diff} days into move"
        
        result = run_scanner_on_date(ticker, scan_date, spy_df)
        
        if result:
            results.append(result)
            print_result_summary(result, breakout_start, days_diff, days_label)
        else:
            failed_dates += 1
    
    if failed_dates > 0:
        print(f"\n⚠️  Warning: {failed_dates}/{len(scan_dates)} dates had insufficient data")
    
    # Summary
    print("\n" + "-"*80)
    print("📊 SUMMARY:")
    
    alerts = [r for r in results if r['alert_triggered']]
    
    if alerts:
        # Find earliest alert
        earliest_alert = alerts[0]
        earliest_date = datetime.strptime(earliest_alert['date'], '%Y-%m-%d')
        days_diff = (earliest_date - breakout_date).days
        
        print(f"✅ Scanner caught this breakout!")
        
        if days_diff < 0:
            print(f"   First alert: {earliest_alert['date']} ({abs(days_diff)} days BEFORE breakout)")
            print(f"   Entry price: ${earliest_alert['current_price']:.2f}")
            entry_to_peak_gain = ((peak_price - earliest_alert['current_price']) / earliest_alert['current_price']) * 100
            print(f"   Peak price: ${peak_price:.2f}")
            print(f"   Potential gain from alert: +{entry_to_peak_gain:.1f}%")
        elif days_diff == 0:
            print(f"   First alert: {earliest_alert['date']} (ON breakout day)")
            print(f"   Entry price: ${earliest_alert['current_price']:.2f}")
            entry_to_peak_gain = ((peak_price - earliest_alert['current_price']) / earliest_alert['current_price']) * 100
            print(f"   Peak price: ${peak_price:.2f}")
            print(f"   Potential gain from breakout day: +{entry_to_peak_gain:.1f}%")
        else:
            print(f"   First alert: {earliest_alert['date']} ({days_diff} days INTO the move)")
            print(f"   Entry price: ${earliest_alert['current_price']:.2f}")
            entry_to_peak_gain = ((peak_price - earliest_alert['current_price']) / earliest_alert['current_price']) * 100
            print(f"   Peak price: ${peak_price:.2f}")
            print(f"   Remaining gain from mid-move entry: +{entry_to_peak_gain:.1f}%")
            print(f"   ⚠️  Scanner caught it late (during the rally, not before)")
        
        # Which signals triggered
        triggered_signals = []
        if earliest_alert['step1_signal']:
            triggered_signals.append("Volume Dry-Up")
        if earliest_alert['step2_signal']:
            triggered_signals.append("Divergences")
        if earliest_alert['step3_signal']:
            triggered_signals.append("Rel. Strength")
        
        print(f"   Winning combo: {', '.join(triggered_signals)}")
        
        # Show all alert dates
        if len(alerts) > 1:
            print(f"\n   Total alerts triggered: {len(alerts)}")
            for alert in alerts:
                alert_date = datetime.strptime(alert['date'], '%Y-%m-%d')
                days_diff = (alert_date - breakout_date).days
                if days_diff < 0:
                    timing = f"{abs(days_diff)}d before"
                elif days_diff == 0:
                    timing = "breakout day"
                else:
                    timing = f"{days_diff}d into move"
                print(f"     • {alert['date']} ({timing}) - Score: {alert['total_score']:.0f}")
    else:
        print(f"❌ Scanner did NOT catch this breakout")
        if results:
            print(f"   Highest score: {max([r['total_score'] for r in results]):.0f}/30")
            print(f"   Most signals: {max([r['signals_met'] for r in results])}/3")
        else:
            print(f"   ⚠️  No valid scan results (data fetching issues)")
            print(f"   Check: Does {ticker} have data for these dates?")
    
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