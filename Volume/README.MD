# Potential Buy Signals

This Python script fetches trading data from the Binance API and identifies potential buy signals based on the following criteria:

1. The trading volume has increased by a specified percentage (e.g., 10%).
2. The current price is above the moving average (e.g., 20 periods).

The script periodically saves the last five potential buy signals to an HTML file that can be opened in a web browser.

## Features

- Fetches 24-hour ticker price change data from the Binance API
- Calculates the moving average for specified trading pairs
- Filters symbols with potential volume increase and above the moving average
- Fetches coin logo URLs from the CoinGecko API
- Generates an HTML file with the last five potential buy signals
- Automatically refreshes the data at a specified interval

## Requirements

- Python 3.x
- Requests library

## Usage

1. Install the Requests library if you don't have it installed:

`` pip install requests ``


2. Edit the following parameters in the script according to your preferences:

`` min_volume_increase_pct = 10 ``
`` fetch_interval = 10 ``
`` moving_average_window = 20 ``


3. Run the script:

`` python3 volume.py ``


4. Open the generated HTML file (`potential_buy_signals.html`) in a web browser.

![Volume Example](https://github.com/dad84/Tradeing-Crypto-Tools/blob/main/Volume/video.webm?raw=true)

## Notes

- This script is for educational purposes only. It does not provide any financial advice or recommendations. Trade at your own risk.
- The Binance API may have rate limits. Make sure not to exceed them by adjusting the `fetch_interval` parameter accordingly.
