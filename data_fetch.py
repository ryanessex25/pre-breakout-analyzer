"""
Data fetcher module - Yahoo Finance (yfinance)
This module can be easily swapped to Polygon.io later
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import config

def fetch_stock_data(ticker, days=None):
    """
    Fetch historical stock data for a given ticker
    
    Args:
        ticker (str): Stock symbol
        days (int): Number of days of historical data (default from config)
    
    Returns:
        pd.DataFrame: OHLCV data with datetime index
    """
    if days is None:
        days = config.DATA_LOOKBACK_DAYS
    
    try:
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # Add buffer for indicators
        
        # Fetch data
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        # Validate data
        if df.empty:
            print(f"⚠️  No data returned for {ticker}")
            return None
        
        # Ensure we have required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            print(f"⚠️  Missing required columns for {ticker}")
            return None
        
        # Remove timezone info if present
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        return df
    
    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {str(e)}")
        return None


def fetch_spy_data(days=None):
    """
    Fetch SPY data for relative strength calculations
    
    Args:
        days (int): Number of days of historical data
    
    Returns:
        pd.DataFrame: SPY OHLCV data
    """
    return fetch_stock_data(config.STEP7_SPY_SYMBOL, days)


def load_ticker_list(filepath=None):
    """
    Load ticker symbols from text file (one ticker per line)
    
    Args:
        filepath (str): Path to ticker list file
    
    Returns:
        list: List of ticker symbols
    """
    if filepath is None:
        filepath = config.TICKER_LIST_PATH
    
    try:
        with open(filepath, 'r') as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        
        print(f"✅ Loaded {len(tickers)} tickers from {filepath}")
        return tickers
    
    except FileNotFoundError:
        print(f"❌ Ticker list file not found: {filepath}")
        return []
    except Exception as e:
        print(f"❌ Error loading ticker list: {str(e)}")
        return []