from scanner import run_scanner, scan_single_stock
from data_fetch import load_ticker_list, fetch_spy_data
from agent import run_agent
from logger import log_decision

def main():
    # Fetch SPY data
    spy_df = fetch_spy_data()
    
    # Load tickers
    tickers = load_ticker_list()[:5]  # Just 5 for now
    
    # Scan stocks
    results = []
    for ticker in tickers:
        result = scan_single_stock(ticker, spy_df)
        if result:
            results.append(result)
    
    print(f"\nScanner found {len(results)} results")
    print("Sending to Claude for analysis...\n")
    
    # Run through LLM
    decisions = run_agent(results)

     # Log each decision
    for d in decisions:
        log_decision(d['ticker'], d['score'], d['decision'])
    
    print(f"\nDone. Claude analyzed {len(decisions)} stocks.")
    
if __name__ == "__main__":
    main()