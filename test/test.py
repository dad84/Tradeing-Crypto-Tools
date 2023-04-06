import requests
import pandas as pd
import numpy as np
import time
import json
import os

def fetch_data_chunks(symbol, interval, limit, num_chunks):
    url = "https://api.binance.com/api/v3/klines"
    data_chunks = []

    for i in range(num_chunks):
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "endTime": None if i == 0 else int(data_chunks[-1][0][0]) - 1
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ValueError(f"Error fetching data for {symbol}: {response.text}")

        data_chunk = response.json()
        if not data_chunk:
            raise ValueError(f"Not enough historical data for {symbol}")

        data_chunks.append(data_chunk)

    return data_chunks

def get_historical_data(symbol, num_chunks=1):
    interval = "1h"
    limit = 1000

    data_chunks = fetch_data_chunks(symbol, interval, limit, num_chunks)
    data = [item for chunk in data_chunks for item in chunk]

    df = pd.DataFrame(data, columns=["Open time", "Open", "High", "Low", "Close", "Volume", "Close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"])
    df["Close"] = df["Close"].astype(float)

    return df

def calculate_moving_averages(df, short_period=10, long_period=50):
    short_mavg = df["Close"].rolling(window=short_period).mean()
    long_mavg = df["Close"].rolling(window=long_period).mean()
    return short_mavg, long_mavg

def moving_average_crossover(short_mavg, long_mavg):
    crossover_above = short_mavg.iloc[-1] > long_mavg.iloc[-1] and short_mavg.iloc[-2] <= long_mavg.iloc[-2]
    crossover_below = short_mavg.iloc[-1] < long_mavg.iloc[-1] and short_mavg.iloc[-2] >= long_mavg.iloc[-2]
    return crossover_above, crossover_below

def get_btc_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    exchange_info = response.json()

    btc_pairs = [symbol_info["symbol"] for symbol_info in exchange_info["symbols"] if symbol_info["quoteAsset"] == "BTC"]

    return btc_pairs

def get_current_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Error fetching current price for {symbol}: {response.text}")
    current_price_data = response.json()
    current_price = float(current_price_data["price"])
    return int(current_price * 1e8)  # convert to satoshis

def scan_market(btc_pairs, num_chunks):
    potential_price_increase = []
    skipped_pairs = {}
    scanned_data = {}

    # Create pairs directory if it doesn't exist
    if not os.path.exists("pairs"):
        os.makedirs("pairs")

    count = 0

    for trading_pair in btc_pairs:
        count += 1
        print(f"Scanning pair {count}/{len(btc_pairs)}")

        # If the pair has been skipped before, skip it again
        if trading_pair in skipped_pairs:
            print(f"{trading_pair}: {skipped_pairs[trading_pair]}")
            continue

        # If the scanned data for the pair exists and is less than 30 minutes old, skip scanning it again
        if trading_pair in scanned_data:
            time_since_scan = time.time() - scanned_data[trading_pair]["timestamp"]
            if time_since_scan < 1800:
                print(f"{trading_pair}: Skipped (data less than 30 minutes old)")
                continue

        try:
            df = get_historical_data(trading_pair, num_chunks)
        except ValueError as e:
            skipped_pairs[trading_pair] = str(e)
            print(f"{trading_pair}: {e}")
            continue

        short_mavg, long_mavg = calculate_moving_averages(df)
        crossover_above, crossover_below = moving_average_crossover(short_mavg, long_mavg)

        if crossover_above:
            potential_price_increase.append(trading_pair)

        # Save the scanned data to file
        filename = f"pairs/{trading_pair}.json"
        with open(filename, "w") as f:
            json.dump(df.to_dict(), f)

        scanned_data[trading_pair] = {
            "data": df.to_dict(),
            "timestamp": time.time()
        }

    print("Scanning complete.")
    return potential_price_increase


def monitor_potential_price_increase(pairs, num_chunks):
    last_market_scan_time = time.time()
    while True:
        print("\nMonitoring potential price increase for:")
        for trading_pair in pairs:
            try:
                current_price = get_current_price(trading_pair)
                print(f"{trading_pair}: Current price is {current_price / 1e8:.8f} BTC ({current_price:,} satoshis)")
            except ValueError as e:
                print(f"{trading_pair}: {e}")

        time_since_last_market_scan = time.time() - last_market_scan_time
        if time_since_last_market_scan >= 1800:  # Re-scan the market every 30 minutes (1800 seconds)
            print("\nRe-scanning the market...\n")
            btc_pairs = get_btc_pairs()
            pairs = scan_market(btc_pairs, num_chunks)
            last_market_scan_time = time.time()

        print("\nWaiting 60 seconds before updating prices...\n")
        time.sleep(60)  # Sleep for 60 seconds

if __name__ == "__main__":
    print("Fetching BTC trading pairs...")
    btc_pairs = get_btc_pairs()
    print(f"Found {len(btc_pairs)} BTC trading pairs.")

    num_chunks = 5

    print("Scanning the market for potential price increase...")
    potential_price_increase = scan_market(btc_pairs, num_chunks)
    scanned_percentage = len(potential_price_increase) / len(btc_pairs) * 100
    print(f"Scanned {scanned_percentage:.2f}% of pairs.")

    if potential_price_increase:
        print(f"Found {len(potential_price_increase)} trading pairs with potential price increase.")
        monitor_potential_price_increase(potential_price_increase, num_chunks)
    else:
        print("No trading pairs with potential price increase found.")