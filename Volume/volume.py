import requests
import json
import time
import os

# Additional imports
from datetime import datetime

# Set the Binance API endpoint
api_url = "https://api.binance.com"
ticker_24hr_endpoint = "/api/v3/ticker/24hr"
klines_endpoint = "/api/v3/klines"

# Set the minimum volume increase percentage (e.g., 10%)
min_volume_increase_pct = 10

# Set the time interval between fetches in seconds (e.g., 10 seconds)
fetch_interval = 10

# Set the moving average window (e.g., 20 periods)
moving_average_window = 20

def fetch_24hr_ticker_price_change():
    response = requests.get(api_url + ticker_24hr_endpoint)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print("Failed to fetch data from Binance API")
        return []

def fetch_klines_data(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": moving_average_window
    }
    response = requests.get(api_url + klines_endpoint, params=params)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to fetch klines data for {symbol}")
        return []

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

def save_html_file(html_content, file_name="potential_buy_signals.html"):
    with open(file_name, "w") as f:
        f.write(html_content)

def main():
    previous_ticker_data = []
    interval = "1h"
    last_5_signals = []
    logo_urls = fetch_coin_logo_urls()

    while True:
        current_ticker_data = fetch_24hr_ticker_price_change()
        potential_symbols = filter_symbols_with_potential_volume_increase(current_ticker_data, previous_ticker_data, min_volume_increase_pct, interval)

        if potential_symbols:
            last_5_signals.append(potential_symbols)
            last_5_signals = last_5_signals[-5:]
            html_content = generate_html_content(last_5_signals, logo_urls)
            save_html_file(html_content)
            print("Saved potential buy signals to HTML file")
        else:
            print("No symbols with potential volume increase and above moving average found")

        previous_ticker_data = current_ticker_data
        print(f"Waiting {fetch_interval} seconds before the next fetch...")
        time.sleep(fetch_interval)

if __name__ == "__main__":
    main()