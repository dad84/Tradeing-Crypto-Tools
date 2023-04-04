# Binance Potential Buy Signals

This Python script is a tool to identify potential cryptocurrency buy signals on the Binance exchange based on sudden volume increases and price movement above a specified moving average.

## Features
- Fetches 24-hour ticker data and klines data from Binance's API
- Filters trading pairs with significant volume increase
- Calculates the moving average and filters pairs with price above the moving average
- Fetches coin logo URLs from CoinGecko API and displays the base coin logo
- Continuously updates the generated HTML file with the latest potential buy signals

## Output
The script generates an HTML file displaying the last 5 potential buy signals, including the following information for each pair:
- Symbol
- Volume change
- Price change
- Direction (Up or Down)
- Moving average
- Current price
- Link to trade the pair on Binance

## Usage
Run the script to continuously fetch data at a specified interval and update the HTML file with the latest potential buy signals.
