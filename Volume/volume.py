import requests
import json
import time

# Set the Binance API endpoint
api_url = "https://api.binance.com"
ticker_24hr_endpoint = "/api/v3/ticker/24hr"

# Set the minimum volume increase percentage (e.g., 10%)
min_volume_increase_pct = 10

# Set the time interval between fetches in seconds (e.g., 60 seconds)
fetch_interval = 60

def fetch_24hr_ticker_price_change():
    response = requests.get(api_url + ticker_24hr_endpoint)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print("Failed to fetch data from Binance API")
        return []

def filter_symbols_with_potential_volume_increase(ticker_data, previous_ticker_data, threshold):
    potential_symbols = []

    if not previous_ticker_data:
        return potential_symbols

    ticker_data_dict = {ticker['symbol']: ticker for ticker in ticker_data}

    for prev_ticker in previous_ticker_data:
        symbol = prev_ticker['symbol']
        prev_quote_volume = float(prev_ticker['quoteVolume'])

        if symbol in ticker_data_dict:
            current_ticker = ticker_data_dict[symbol]
            current_quote_volume = float(current_ticker['quoteVolume'])

            if prev_quote_volume != 0:
                volume_change_pct = (current_quote_volume - prev_quote_volume) / prev_quote_volume * 100

                if volume_change_pct >= threshold:
                    potential_symbols.append({
                        'symbol': symbol,
                        'volume_change_pct': volume_change_pct,
                        'price_change_pct': float(current_ticker['priceChangePercent'])
                    })

    return potential_symbols

def main():
    previous_ticker_data = []

    while True:
        current_ticker_data = fetch_24hr_ticker_price_change()
        potential_symbols = filter_symbols_with_potential_volume_increase(current_ticker_data, previous_ticker_data, min_volume_increase_pct)

        if potential_symbols:
            print("Symbols with potential volume increase:")
            for symbol in potential_symbols:
                print(f"Symbol: {symbol['symbol']}, Volume Change: {symbol['volume_change_pct']}%, Price Change: {symbol['price_change_pct']}%")
        else:
            print("No symbols with potential volume increase found")

        previous_ticker_data = current_ticker_data
        print(f"Waiting {fetch_interval} seconds before the next fetch...")
        time.sleep(fetch_interval)

if __name__ == "__main__":
    main()