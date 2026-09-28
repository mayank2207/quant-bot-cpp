import csv
import os
from datetime import datetime

LOG_FILE = "trades.csv"

def log_trade(action, symbol, price, reason):
    """Appends order details to trades.csv"""
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        # Write CSV header if creating file for the first time
        if not file_exists:
            writer.writerow(["Timestamp (UTC)", "Symbol", "Action", "Price", "Reason"])
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, symbol, action, f"{price:.2f}", reason])
    
    print(f"[LOGGED] Trade saved to {LOG_FILE}")

def execute_order(action, symbol, price, reason="Strategy Signal"):
    """Simulate order execution & record trade log"""
    global in_position
    print("\n" + "=" * 50)
    print(f" [ORDER EXECUTED] Action: {action} | Symbol: {symbol} | Price: ${price:.2f} | Reason: {reason}")
    print("=" * 50 + "\n")
    
    if action == "BUY":
        in_position = True
    elif action == "SELL":
        in_position = False

    # Save to local CSV log file
    log_trade(action, symbol, price, reason)