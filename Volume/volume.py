# This script fetches 24-hour ticker price change statistics from the Binance API, filters symbols
# with potential volume increase above a given threshold, calculates the moving average for each symbol,
# and generates an HTML report with potential buy signals.
import requests
import json
import time
import os
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.utils import dropna
import pandas as pd

# Set the Binance API endpoint
api_url = "https://api.binance.com"
ticker_24hr_endpoint = "/api/v3/ticker/24hr"
klines_endpoint = "/api/v3/klines"

min_volume_increase_pct = 10
fetch_interval = 10
moving_average_window = 20
rsi_lower_threshold = 30
macd_cross_threshold = 0

# Fetch klines (candlestick) data for a symbol from the Binance API
def fetch_klines_data(symbol, interval, limit=None):
    params = {
       "symbol": symbol,
       "interval": interval,
    }
    if limit is not None:
        params["limit"] = limit

    response = requests.get(api_url + klines_endpoint, params=params)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to fetch klines data for {symbol}")
        return []

def calculate_rsi(symbol, interval, window):
    klines_data = fetch_klines_data(symbol, interval, window + 1)
    if not klines_data:
        return None

    closing_prices = [float(kline[4]) for kline in klines_data]
    df = pd.DataFrame(closing_prices, columns=["close"])
    rsi = RSIIndicator(df["close"], window)
    return rsi.rsi().iloc[-1]

def calculate_macd_cross(symbol, interval, window):
    klines_data = fetch_klines_data(symbol, interval, window * 3)
    if not klines_data:
        return None

    closing_prices = [float(kline[4]) for kline in klines_data]
    df = pd.DataFrame(closing_prices, columns=["close"])
    df.dropna(inplace=True)  # Drop NaN values from the DataFrame
    macd = MACD(df["close"], window_slow=window, window_fast=window // 2, window_sign=window // 4)
    macd_diff = macd.macd_diff().iloc[-1]

    return macd_diff

def check_potential_price_increase(symbol, interval):
    rsi = calculate_rsi(symbol, interval, moving_average_window)
    macd_cross = calculate_macd_cross(symbol, interval, moving_average_window)

    if rsi is None or macd_cross is None:
        return False

    if rsi <= rsi_lower_threshold and macd_cross > macd_cross_threshold:
        return True

    return False
    
# Fetch 24-hour ticker price change statistics from the Binance API    
def fetch_24hr_ticker_price_change():
    response = requests.get(api_url + ticker_24hr_endpoint)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print("Failed to fetch data from Binance API")
        return []
    
# Calculate the moving average for a symbol based on the given klines data
def calculate_moving_average(symbol, interval):
    klines_data = fetch_klines_data(symbol, interval)
    if not klines_data:
        return None

    closing_prices = [float(kline[4]) for kline in klines_data]
    moving_average = sum(closing_prices) / len(closing_prices)
    return moving_average

def filter_symbols_with_potential_volume_increase(ticker_data, previous_ticker_data, threshold, interval):
    potential_symbols = []

    if not previous_ticker_data:
        return potential_symbols

    ticker_data_dict = {ticker['symbol']: ticker for ticker in ticker_data}

    for prev_ticker in previous_ticker_data:
        symbol = prev_ticker['symbol']
        prev_quote_volume = float(prev_ticker['quoteVolume'])

        if symbol in ticker_data_dict and symbol.endswith('BTC'):  # Only consider symbols ending with 'BTC'
            current_ticker = ticker_data_dict[symbol]
            current_quote_volume = float(current_ticker['quoteVolume'])

            if prev_quote_volume != 0:
                volume_change_pct = (current_quote_volume - prev_quote_volume) / prev_quote_volume * 100

                if volume_change_pct >= threshold:
                    price_change_pct = float(current_ticker['priceChangePercent'])
                    price_direction = "Up" if price_change_pct > 0 else "Down"

                    moving_average = calculate_moving_average(symbol, interval)
                    current_price = float(current_ticker['lastPrice'])

                    if moving_average and current_price > moving_average:
                        potential_symbols.append({
                            'symbol': symbol,
                            'volume_change_pct': volume_change_pct,
                            'price_change_pct': price_change_pct,
                            'price_direction': price_direction,
                            'moving_average': moving_average,
                            'current_price': current_price,
                            'exchange_link': f"https://www.binance.com/en/trade/{symbol}"
                        })

    return potential_symbols

def filter_symbols_with_potential_price_increase(ticker_data, interval):
    potential_symbols = []

    for ticker in ticker_data:
        symbol = ticker['symbol']

        if symbol.endswith('BTC'):  # Only consider symbols ending with 'BTC'
            if check_potential_price_increase(symbol, interval):
                current_price = float(ticker['lastPrice'])
                potential_symbols.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'exchange_link': f"https://www.binance.com/en/trade/{symbol}"
                })

    return potential_symbols

# Fetch coin logo URLs from the CoinGecko API
def fetch_coin_logo_urls():
    coingecko_api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "btc", "order": "market_cap_desc", "per_page": 200, "page": 1, "sparkline": False}
    response = requests.get(coingecko_api_url, params=params)

    if response.status_code == 200:
        coin_data = json.loads(response.text)
        logo_urls = {coin['symbol'].upper(): coin['image'] for coin in coin_data}
        return logo_urls
    else:
        print("Failed to fetch coin logo URLs from CoinGecko API")
        return {}

def generate_html_content(last_5_signals, logo_urls):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="{fetch_interval}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Potential Buy Signals - {current_time}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}

        h1 {{
            background-color: #333;
            color: #fff;
            padding: 20px;
            margin: 0;
        }}

        h2 {{
            padding: 10px;
            background-color: #f7f7f7;
            margin: 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}

        tbody tr:nth-child(even) {{
            background-color: #f7f7f7;
        }}

        tbody tr:hover {{
            background-color: #ddd;
        }}

        a {{
            text-decoration: none;
            color: #0066cc;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}

        .up {{
            color: green;
        }}

        .down {{
            color: red;
        }}
    </style>
</head>
<body>
    <h1>Potential Buy Signals - {current_time}</h1>
"""

    for idx, potential_symbols in enumerate(reversed(last_5_signals), 1):
        html_content += f"<h2>Signal {idx}</h2>"
        html_content += """
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Volume Change</th>
                <th>Price Change</th>
                <th>Direction</th>
                <th>Moving Average</th>
                <th>Current Price</th>
                <th>Exchange Link</th>
            </tr>
        </thead>
        <tbody>
"""

        for symbol in potential_symbols:
            formatted_current_price = f"{symbol['current_price']:.8f}"
            formatted_moving_average = f"{symbol['moving_average']:.8f}"
            direction_class = "up" if symbol['price_direction'] == "Up" else "down"
            base_coin_symbol = symbol['symbol'][:-3]  # Remove 'BTC' from the symbol to get the base coin symbol
            coin_logo_url = logo_urls.get(base_coin_symbol, "")  # Get the logo URL for the base coin


            html_content += f"""
            <tr class="{direction_class}">
                <td><img src="{coin_logo_url}" alt="{base_coin_symbol} logo" width="24" height="24"> {symbol['symbol']}</td>
                <td>{symbol['volume_change_pct']}%</td>
                <td>{symbol['price_change_pct']}%</td>
                <td>{symbol['price_direction']}</td>
                <td>{formatted_moving_average}</td>
                <td>{formatted_current_price}</td>
                <td><a href="{symbol['exchange_link']}">Trade on Binance</a></td>
            </tr>
"""
        html_content += """
        </tbody>
    </table>
"""
    html_content += """

</body>
</html>
"""
    return html_content
    
# Save the generated HTML content to a file
def save_html_file(html_content, file_name="potential_buy_signals.html"):
    with open(file_name, "w") as f:
        f.write(html_content)
        
# Main function to fetch data, filter symbols, and generate the HTML report
def main():
    interval = "1h"
    last_5_signals = []
    logo_urls = fetch_coin_logo_urls()

    previous_ticker_data = []

    while True:
        current_ticker_data = fetch_24hr_ticker_price_change()
        potential_symbols = filter_symbols_with_potential_volume_increase(
            current_ticker_data, previous_ticker_data, min_volume_increase_pct, interval
        )

        if potential_symbols:
            last_5_signals.append(potential_symbols)
            last_5_signals = last_5_signals[-5:]
            html_content = generate_html_content(last_5_signals, logo_urls)
            save_html_file(html_content)
            print("Saved potential price increase signals to HTML file")
        else:
            print("No symbols with potential price increase found")

        previous_ticker_data = current_ticker_data

        print(f"Waiting {fetch_interval} seconds before the next fetch...")
        time.sleep(fetch_interval)
        
# Run the main function when the script is executed
if __name__ == "__main__":
    main()