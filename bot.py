import time
import csv
import os
from datetime import datetime
import requests
import config

LOG_FILE = "trades.csv"

# Strategy Parameters
SHORT_WINDOW = 5
LONG_WINDOW = 20
STOP_LOSS_PCT = 0.02    # 2% Stop-Loss
TAKE_PROFIT_PCT = 0.04  # 4% Take-Profit

price_history = []
in_position = False
entry_price = 0.0

def get_roostoo_ticker(pair="BTC/USD"):
    """Fetch live ticker price with Roostoo timestamp & Binance fallback"""
    timestamp = int(time.time() * 1000)
    
    # 1. Primary: Fetch from Roostoo API
    try:
        url = f"{config.BASE_URL}/v3/ticker"
        params = {"pair": pair, "timestamp": timestamp}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                if "price" in data:
                    return float(data["price"])
                elif pair in data and isinstance(data[pair], dict) and "price" in data[pair]:
                    return float(data[pair]["price"])
    except Exception as e:
        print(f"[Roostoo Timeout/Error] {e} | Switching to market price fallback...")

    # 2. Fallback: Fetch real-time BTC price from Binance Public API
    try:
        binance_symbol = pair.replace("/", "").replace("USD", "USDT")
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return float(response.json().get("price", 0))
    except Exception as e:
        print(f"[Fallback Error] Failed to fetch price: {e}")

    return None

def send_roostoo_order(pair, side, quantity, price):
    """Places an order on Roostoo API"""
    url = f"{config.BASE_URL}/v3/place_order"
    payload = {
        "pair": pair,
        "side": side.upper(),       # "BUY" or "SELL"
        "type": "LIMIT",
        "quantity": str(quantity),
        "price": str(price)
    }
    headers, signed_payload = config.get_signed_headers(payload)
    
    try:
        response = requests.post(url, headers=headers, data=signed_payload, timeout=10)
        print(f"[Roostoo Order Response] Status: {response.status_code} | Body: {response.text}")
        return response.json()
    except Exception as e:
        print(f"[Order Error] Failed to execute Roostoo order: {e}")
        return None

def log_trade(action, symbol, price, reason):
    """Records trade history locally to trades.csv"""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp (UTC)", "Symbol", "Action", "Price", "Reason"])
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, symbol, action, f"{price:.2f}", reason])
    print(f"[LOGGED] Trade appended to {LOG_FILE}")

def execute_order(action, symbol, price, reason="Strategy Signal"):
    """Triggers Roostoo API order & records trade log"""
    global in_position
    print("\n" + "=" * 50)
    print(f" [ORDER SIGNAL] Action: {action} | Symbol: {symbol} | Price: ${price:.2f} | Reason: {reason}")
    print("=" * 50 + "\n")
    
    # Send order to Roostoo API
    send_roostoo_order(pair=symbol, side=action, quantity=0.01, price=price)
    
    if action == "BUY":
        in_position = True
    elif action == "SELL":
        in_position = False

    log_trade(action, symbol, price, reason)

def calculate_sma(prices, window):
    if len(prices) < window:
        return 0.0
    return sum(prices[-window:]) / window

def evaluate_strategy(current_price, symbol="BTC/USD"):
    global in_position, entry_price
    
    price_history.append(current_price)
    if len(price_history) > 100:
        price_history.pop(0)

    if len(price_history) < LONG_WINDOW:
        print(f"[Gathering Data] {len(price_history)}/{LONG_WINDOW} ticks collected... Current Price: ${current_price:.2f}")
        return

    # Check Risk Controls
    if in_position and entry_price > 0:
        pnl_pct = (current_price - entry_price) / entry_price
        
        if pnl_pct <= -STOP_LOSS_PCT:
            print(f">>> RISK SIGNAL: STOP-LOSS TRIGGERED ({pnl_pct*100:.2f}%) <<<")
            execute_order("SELL", symbol, current_price, "Stop-Loss Triggered")
            entry_price = 0.0
            return

        elif pnl_pct >= TAKE_PROFIT_PCT:
            print(f">>> RISK SIGNAL: TAKE-PROFIT TRIGGERED (+{pnl_pct*100:.2f}%) <<<")
            execute_order("SELL", symbol, current_price, "Take-Profit Triggered")
            entry_price = 0.0
            return

    short_sma = calculate_sma(price_history, SHORT_WINDOW)
    long_sma = calculate_sma(price_history, LONG_WINDOW)

    print(f"[Strategy Check] Price: ${current_price:.2f} | Short SMA: ${short_sma:.2f} | Long SMA: ${long_sma:.2f}")

    if short_sma > long_sma and not in_position:
        print(">>> SIGNAL: Golden Cross (BUY) <<<")
        execute_order("BUY", symbol, current_price, "Golden Cross")
        entry_price = current_price

    elif short_sma < long_sma and in_position:
        print(">>> SIGNAL: Death Cross (SELL) <<<")
        execute_order("SELL", symbol, current_price, "Death Cross")
        entry_price = 0.0

def main():
    print(f"Starting Quantitative Trading Bot in [{config.MODE}] mode...")
    print(f"Target Symbol: BTC/USD | Short SMA: {SHORT_WINDOW} | Long SMA: {LONG_WINDOW}\n")
    
    while True:
        try:
            price = get_roostoo_ticker("BTC/USD")
            if price and price > 0:
                evaluate_strategy(price, "BTC/USD")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nBot terminated by user.")
            break
        except Exception as e:
            print(f"Unexpected Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()