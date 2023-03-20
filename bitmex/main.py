import time
import hmac
import hashlib
import requests
import json
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

# Set Bitmex API credentials
api_key = 'api_key'
api_secret = 'api_secret'

# Define Bitmex API endpoints
api_base_url = 'https://testnet.bitmex.com/api/v1'
api_orders_url = api_base_url + '/order'
api_instrument_url = api_base_url + '/instrument'

# Download NLTK data
nltk.download('vader_lexicon')

# Define trading parameters
symbol = 'XBTUSD'
quantity = 100
long_ma_period = 20
short_ma_period = 10
buy_threshold = 0.01
sell_threshold = -0.01

# Risk management parameters
stop_loss_percentage = 0.10  # 10% stop-loss

# Fundamental analysis parameters
news_api_key = 'api_key'  # Replace with your own News API key
news_base_url = 'https://newsapi.org/v2/everything'

# Define authentication function
def authenticate():
    expires = str(int(round(time.time())) + 5)
    verb = 'GET'
    path = '/api/v1/order'
    data = ''
    message = verb + path + expires + data
    signature = hmac.new(api_secret.encode(), message.encode(), digestmod=hashlib.sha256).hexdigest()
    headers = {
        'api-expires': expires,
        'api-key': api_key,
        'api-signature': signature,
        'Content-Type': 'application/json'
    }
    print(f'message: {message}, signature: {signature}')
    return headers

# Define function to get market data
def get_market_data():
    response = requests.get(api_instrument_url + '?symbol=' + symbol)
    data = response.json()[0]
    return {'last_price': data['lastPrice'], 'mid_price': data['midPrice'], 'buy_price': data['bidPrice'], 'sell_price': data['askPrice']}

api_trade_bucketed_url = api_base_url + '/trade/bucketed'

# Define function to calculate moving averages
def calculate_moving_averages():
    response = requests.get(api_trade_bucketed_url + '?binSize=1d&partial=false&symbol=' + symbol + '&count=' + str(long_ma_period + short_ma_period - 1 + 50) + '&reverse=true')
    data = response.json()
    close_key = 'close' if 'close' in data[0] else 'lastPrice'
    long_ma = sum([d[close_key] for d in data[:long_ma_period]]) / long_ma_period
    short_ma = sum([d[close_key] for d in data[long_ma_period - 1:long_ma_period + short_ma_period - 1]]) / short_ma_period
    return {'long_ma': long_ma, 'short_ma': short_ma}

# Define function to get news sentiment
def get_news_sentiment(keyword):
    sentiment_analyzer = SentimentIntensityAnalyzer()
    url = f"{news_base_url}?q={keyword}&apiKey={news_api_key}"
    response = requests.get(url)
    response_data = response.json()

    if 'articles' not in response_data:
        print(f"Error getting news articles: {response_data}")
        return 0

    articles = response_data['articles']
    sentiments = []

    for article in articles:
        sentiment = sentiment_analyzer.polarity_scores(article['title'])
        sentiments.append(sentiment['compound'])

    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    return avg_sentiment

def is_breakout(symbol, period, last_price):
    response = requests.get(api_instrument_url + '?symbol=' + symbol + '&count=' + str(period))
    data = response.json()
    close_key = 'close' if 'close' in data[0] else 'lastPrice'
    prices = [d[close_key] for d in data]

    highest_price = max(prices)
    lowest_price = min(prices)

    breakout_up = last_price > highest_price
    breakout_down = last_price < lowest_price

    return breakout_up, breakout_down

# Define function to place limit order
def place_limit_order(side, price):
    order_data = {'symbol': symbol, 'orderQty': quantity, 'price': price, 'ordType': 'Limit', 'side': side}
    expires = str(int(round(time.time())) + 5)
    verb = 'POST'
    path = '/api/v1/order'
    data = json.dumps(order_data)
    message = verb + path + expires + data
    signature = hmac.new(api_secret.encode(), message.encode(), digestmod=hashlib.sha256).hexdigest()
    headers = {
        'api-expires': expires,
        'api-key': api_key,
        'api-signature': signature,
        'Content-Type': 'application/json'
    }
    response = requests.post(api_orders_url, headers=headers, json=order_data)
    order_status = response.json()
    print(order_status)

# Define main function
def main():
    while True:
        # Get market data
        market_data = get_market_data()
        print(market_data)

        # Calculate moving averages
        ma_data = calculate_moving_averages()
        print(ma_data)

        # Get news sentiment
        news_sentiment = get_news_sentiment(symbol)
        print(f"News sentiment: {news_sentiment}")

        # Detect breakouts
        breakout_up, breakout_down = is_breakout(symbol, long_ma_period, market_data['last_price'])
        print(f"Breakout up: {breakout_up}, Breakout down: {breakout_down}")

        # Place orders based on moving average crossover strategy, news sentiment, and breakouts
        if ma_data['short_ma'] > ma_data['long_ma'] * (1 + buy_threshold) and news_sentiment > 0 and breakout_up:
            place_limit_order('Buy', market_data['buy_price'])
            stop_loss_price = market_data['buy_price'] * (1 - stop_loss_percentage)
            place_limit_order('Stop', stop_loss_price)

        elif ma_data['short_ma'] < ma_data['long_ma'] * (1 + sell_threshold) and news_sentiment < 0 and breakout_down:
            place_limit_order('Sell', market_data['sell_price'])
            stop_loss_price = market_data['sell_price'] * (1 + stop_loss_percentage)
            place_limit_order('Stop', stop_loss_price)

        # Wait for next iteration
        time.sleep(900)

if __name__ == '__main__':
    main()
