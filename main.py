import csv
import os
from datetime import datetime
from scanner import scan_single_stock
from data_fetch import load_ticker_list, fetch_spy_data
from agent import run_agent
from logger import log_decision


SCAN_LOG_FILE = "results/scan_results.csv"


def save_scan_results(results):
    """Save raw scanner results to CSV"""
    if not results:
        return

    os.makedirs("results", exist_ok=True)
    file_exists = os.path.exists(SCAN_LOG_FILE)

    fieldnames = [
        'date', 'ticker', 'alert_level', 'total_score',
        'volume_score', 'momentum_score', 'rs_score',
        'rsi_current', 'obv_days_rising', 'price_above_ema',
        'outperformance_short', 'outperformance_long',
        'current_price', 'volume'
    ]

    with open(SCAN_LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        for result in results:
            result['date'] = datetime.now().strftime('%Y-%m-%d')
            writer.writerow(result)

    print(f"💾 Scan results saved to {SCAN_LOG_FILE}")


def main():
    # Fetch SPY data
    spy_df = fetch_spy_data()

    # Load tickers
    tickers = load_ticker_list()[:5]

    # Scan stocks
    results = []
    for ticker in tickers:
        result = scan_single_stock(ticker, spy_df)
        if result:
            results.append(result)

    print(f"\nScanner found {len(results)} results above threshold")

    # Save raw scan results
    save_scan_results(results)

    print("Sending to Claude for analysis...\n")

    # Run through LLM
    decisions = run_agent(results)

    # Log each decision
    for d in decisions:
        log_decision(d['ticker'], d['score'], d['decision'])

    print(f"\nDone. Claude analyzed {len(decisions)} stocks.")


if __name__ == "__main__":
    main()