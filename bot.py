import csv
import json
import os
import time
from datetime import datetime
import requests

# ==========================================
# 1. CONFIGURATION & KEYS LOADER
# ==========================================
def load_config():
    """Load API credentials and base URL from config.json"""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[Warning] config.json not found. Using fallback endpoint.")
        return {
            "api_key": "MOCK_KEY",
            "secret_key": "MOCK_SECRET",
            "base_url": "https://api.binance.com/api/v3"
        }

config = load_config()
BASE_URL = config.get("base_url", "https://api.binance.com/api/v3")

# ==========================================
# 2. TRADE LOGGING SETUP
# ==========================================
LOG_FILE = "trades.csv"

def init_log_file():
    """Initialize CSV log file with headers if it doesn't exist"""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "action", "symbol", "price", "status"])

def log_trade(action, symbol, price, status="EXECUTED"):
    """Append executed order details to CSV file"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, action, symbol, price, status])
    print(f"[Log Saved] Recorded {action} at ${price:.2f} in {LOG_FILE}")

# ==========================================
# 3. GLOBAL STATE & STRATEGY PARAMETERS
# ==========================================
price_history = []
SHORT_WINDOW = 5
LONG_WINDOW = 20
in_position = False

# ==========================================
# 4. MARKET DATA API FETCHING
# ==========================================
def get_latest_price(symbol="BTCUSDT"):
    """Fetch current market price from API"""
    try:
        if "binance" in BASE_URL:
            url = f"{BASE_URL}/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return float(response.json()["price"])
        else:
            url = f"{BASE_URL}/v3/ticker?symbol=BTC/USDT"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return float(response.json().get("price", 0))
    except Exception as e:
        print(f"[API Error] Failed to fetch price: {e}")
    return None

# ==========================================
# 5. TECHNICAL INDICATORS & STRATEGY LOGIC
# ==========================================
def calculate_sma(prices, window):
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

def execute_order(action, symbol, price):
    global in_position
    print("\n" + "=" * 50)
    print(f" [ORDER EXECUTED] Action: {action} | Symbol: {symbol} | Price: ${price:.2f}")
    print("=" * 50 + "\n")
    
    if action == "BUY":
        in_position = True
    elif action == "SELL":
        in_position = False

    # Record trade into trades.csv
    log_trade(action, symbol, price)

def evaluate_strategy(current_price, symbol="BTCUSDT"):
    global in_position
    price_history.append(current_price)
    
    if len(price_history) > 100:
        price_history.pop(0)

    if len(price_history) < LONG_WINDOW:
        print(f"[Gathering Data] {len(price_history)}/{LONG_WINDOW} price points collected...")
        return

    short_sma = calculate_sma(price_history, SHORT_WINDOW)
    long_sma = calculate_sma(price_history, LONG_WINDOW)

    print(f"[Strategy Check] Price: ${current_price:.2f} | Short SMA: ${short_sma:.2f} | Long SMA: ${long_sma:.2f}")

    # Golden Cross: Fast SMA crosses ABOVE Slow SMA -> BUY
    if short_sma > long_sma and not in_position:
        print(">>> SIGNAL: Golden Cross (BUY)")
        execute_order("BUY", symbol, current_price)

    # Death Cross: Fast SMA crosses BELOW Slow SMA -> SELL
    elif short_sma < long_sma and in_position:
        print(">>> SIGNAL: Death Cross (SELL)")
        execute_order("SELL", symbol, current_price)

    else:
        status = "Holding Position" if in_position else "Waiting for Signal"
        print(f"[Status] {status}")

# ==========================================
# 6. MAIN EXECUTION LOOP
# ==========================================
def main():
    init_log_file()
    print("Starting Quantitative Trading Bot with Trade Logging...")
    print(f"Logging outputs to: {LOG_FILE}\n")
    
    while True:
        try:
            price = get_latest_price("BTCUSDT")
            if price is not None:
                evaluate_strategy(price, "BTCUSDT")
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n[Bot Stopped] Terminated by user.")
            break
        except Exception as e:
            print(f"[Loop Error] {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()