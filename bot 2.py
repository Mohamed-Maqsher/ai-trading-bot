import os
import time
import schedule
import threading
from dotenv import load_dotenv
from telegram_alerts import send_alert
from lstm_predict import predict_lstm
import ccxt
from datetime import datetime

load_dotenv()

# Coinbase credentials from .env
api_key = os.getenv("COINBASE_API_KEY")
secret = os.getenv("COINBASE_SECRET")
password = os.getenv("COINBASE_PASSPHRASE")

coinbase = ccxt.coinbase({
    'apiKey': api_key,
    'secret': secret,
    'password': password,
    'enableRateLimit': True
})

PAIR = 'ETH/USD'
DEFAULT_TRADE_AMOUNT = 200
MAX_TRADE_AMOUNT = 300
STOP_LOSS_PCT = 0.05

position = None

def get_balance():
    balance = coinbase.fetch_balance()
    return balance['USD']['free']

def place_order(amount_usd, side):
    ticker = coinbase.fetch_ticker(PAIR)
    price = ticker['last']
    qty = round(amount_usd / price, 6)

    order = None
    if side == 'buy':
        order = coinbase.create_market_buy_order(PAIR, qty)
    elif side == 'sell':
        order = coinbase.create_market_sell_order(PAIR, qty)
    return order, price, qty

def log_trade(action, price, qty, reason):
    with open("logs/trades.csv", "a") as f:
        f.write(f"{datetime.utcnow()},{PAIR},{action},{price},{qty},{reason}\n")

def trade_logic():
    global position

    confidence = predict_lstm()
    balance = get_balance()

    # If no position
    if not position and confidence > 0.6:
        amount = DEFAULT_TRADE_AMOUNT
        if confidence > 0.85:
            amount = MAX_TRADE_AMOUNT
        if balance < amount:
            send_alert("⚠️ Not enough balance to trade.")
            return

        order, price, qty = place_order(amount, "buy")
        position = {'entry': price, 'qty': qty}
        send_alert(f"🟢 BUY {qty} ETH @ ${price:.2f} | Confidence: {confidence:.2f}")
        log_trade("BUY", price, qty, f"confidence={confidence:.2f}")

    # If holding position
    elif position:
        current_price = coinbase.fetch_ticker(PAIR)['last']
        entry = position['entry']
        if current_price <= entry * (1 - STOP_LOSS_PCT):
            order, price, qty = place_order(position['qty'] * current_price, "sell")
            send_alert(f"🔻 STOP LOSS SELL {qty} ETH @ ${price:.2f}")
            log_trade("SELL", price, qty, "stop-loss")
            position = None

def retrain():
    os.system("python3 lstm_train.py")

schedule.every().day.at("09:00").do(retrain)

def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=schedule_thread, daemon=True).start()

while True:
    trade_logic()
    time.sleep(60)
