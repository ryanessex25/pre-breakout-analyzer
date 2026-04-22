import csv
import os
from datetime import datetime

LOG_FILE = "results/decision_log.csv"

def log_decision(ticker, score, decision):
    """
    Logs a Claude trade decision to CSV
    """
    
    # Create results folder if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Check if file exists to write header
    file_exists = os.path.exists(LOG_FILE)
    
    # Parse decision text into fields
    lines = decision.strip().split('\n')
    parsed = {}
    for line in lines:
        if ':' in line:
            key, _, value = line.partition(':')
            parsed[key.strip()] = value.strip()
    
    row = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ticker': ticker,
        'decision': parsed.get('Decision', ''),
        'confidence': parsed.get('Confidence', ''),
        'entry_zone': parsed.get('Entry zone', ''),
        'stop_loss': parsed.get('Stop loss', ''),
        'target': parsed.get('Target', ''),
        'reasoning': parsed.get('Reasoning', ''),
        'outcome': ''  # You fill this in later manually
    }
    
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    
    print(f"📝 Logged decision for {ticker}")