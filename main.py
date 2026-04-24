import csv
import os
from datetime import datetime
from scanner import scan_single_stock
from data_fetch import load_ticker_list, fetch_spy_data
from agent import run_agent
from logger import log_decision
import argparse

# The orchestrator
# -----------------

SCAN_LOG_FILE = "results/scan_results.csv"


def save_scan_results(results):
    """Save raw scanner results to CSV"""
    if not results:
        return

    os.makedirs("results", exist_ok=True)
    file_exists = os.path.exists(SCAN_LOG_FILE)

    fieldnames = [
        'date', 'ticker',
        # Volume
        'red_volume_ratio', 'price_above_ema', 'red_day_avg_volume',
        'red_day_volume_slope', 'red_day_stepdown_count', 'red_day_count',
        # Momentum
        'rsi_current', 'rsi_slope', 'price_slope',
        'macd_histogram', 'macd_histogram_prev', 'obv_days_rising',
        # Relative Strength
        'outperformance_short', 'outperformance_long',
        'rs_slope_short', 'rs_slope_long',
        # Compression
        'atr_contracting', 'atr_today', 'atr_lookback',
        'near_recent_high', 'pct_from_high_10d', 'pct_from_high_20d',
        'pct_from_52w_high', 'near_52w_high', 'week_52_high',
        # Price
        'current_price', 'volume'
    ]

    with open(SCAN_LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        for result in results:
            result['date'] = datetime.now().strftime('%Y-%m-%d')
            writer.writerow(result)

    print(f"Scan results saved to {SCAN_LOG_FILE}")


def main(limit=5, offset=0):
    # Fetch SPY data
    spy_df = fetch_spy_data()

    # Load tickers
    tickers = load_ticker_list()[offset:offset+limit]

    # Scan stocks
    results = []
    for ticker in tickers:
        result = scan_single_stock(ticker, spy_df)
        if result:
            results.append(result)

    print(f"\nScanner found {len(results)} results")

    # Save raw scan results
    save_scan_results(results)

    print("Sending to Claude for analysis...\n")

    # Run through LLM
    decisions = run_agent(results)

    # Log each decision
    for d in decisions:
        log_decision(d['ticker'], d['decision'])

    print(f"\nDone. Claude analyzed {len(decisions)} stocks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()
    main(limit=args.limit, offset=args.offset)