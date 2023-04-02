import requests
import json
import time

# Set the Binance API endpoint
api_url = "https://api.binance.com"
ticker_24hr_endpoint = "/api/v3/ticker/24hr"
klines_endpoint = "/api/v3/klines"

# Set the minimum volume increase percentage (e.g., 10%)
min_volume_increase_pct = 10

# Set the time interval between fetches in seconds (e.g., 60 seconds)
fetch_interval = 60

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

def main():
    previous_ticker_data = []
    interval = "1h"  # Set the interval for the moving average calculation (e.g., 1 hour)

    while True:
        current_ticker_data = fetch_24hr_ticker_price_change()
        potential_symbols = filter_symbols_with_potential_volume_increase(current_ticker_data, previous_ticker_data, min_volume_increase_pct, interval)

        if potential_symbols:
            print("Symbols with potential volume increase and above moving average:")
            for symbol in potential_symbols:
                print(f"Symbol: {symbol['symbol']}, Volume Change: {symbol['volume_change_pct']}%, Price Change: {symbol['price_change_pct']}%, Direction: {symbol['price_direction']}, Moving Average: {symbol['moving_average']}, Current Price: {symbol['current_price']}, Exchange Link: {symbol['exchange_link']}")
        else:
            print("No symbols with potential volume increase and above moving average found")

        previous_ticker_data = current_ticker_data
        print(f"Waiting {fetch_interval} seconds before the next fetch...")
        time.sleep(fetch_interval)

if __name__ == "__main__":
    main()
