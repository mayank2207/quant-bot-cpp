import time
import requests

# List to store historical prices for averages
price_history = []

def get_ticker_price(symbol="BTCUSDT"):
    """Fetch live ticker price from Binance test feed"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return float(response.json()["price"])
    except Exception as e:
        print(f"Fetch error: {e}")
    return None

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def evaluate_trading_strategy(current_price):
    """Moving Average Crossover Strategy"""
    price_history.append(current_price)
    
    # Keep only the last 30 prices in memory
    if len(price_history) > 30:
        price_history.pop(0)

    # Need at least 15 price points to start calculating
    if len(price_history) < 15:
        print(f"Collecting market data... ({len(price_history)}/15 gathered)")
        return

    # Calculate 5-period (fast) and 15-period (slow) moving averages
    fast_sma = calculate_sma(price_history, period=5)
    slow_sma = calculate_sma(price_history, period=15)

    print(f"Fast SMA (5): ${fast_sma:.2f} | Slow SMA (15): ${slow_sma:.2f}")

    # Trading Signal Rules
    if fast_sma > slow_sma:
        print(">>> SIGNAL: BUY (Bullish Trend Detected) <<<")
    elif fast_sma < slow_sma:
        print(">>> SIGNAL: SELL (Bearish Trend Detected) <<<")
    else:
        print("SIGNAL: HOLD (Neutral Market)")

def main():
    print("Starting Quantitative Strategy Bot...")
    
    while True:
        try:
            price = get_ticker_price("BTCUSDT")
            
            if price is not None:
                print(f"\n[Price Update] BTC: ${price}")
                evaluate_trading_strategy(price)
            
            time.sleep(5) # Fetch every 5 seconds
            
        except KeyboardInterrupt:
            print("\nBot execution stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()