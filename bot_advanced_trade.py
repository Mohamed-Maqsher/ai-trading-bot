import os
import time
import hmac
import json
import base64
import hashlib
import requests
import logging
from datetime import datetime
from urllib.parse import urljoin
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)

# === Load Env Vars ===
API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
EC_PRIVATE_KEY = os.getenv("COINBASE_PRIVATE_KEY").replace("\n", "\n").encode()
ORG_ID = os.getenv("COINBASE_ORG_ID")
TRADING_PAIR = os.getenv("TRADING_PAIR", "ETH-USD")
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", 200))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 0.05))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Coinbase API Base ===
BASE_URL = "https://api.coinbase.com"

# === Load and Parse EC Private Key ===
private_key = serialization.load_pem_private_key(
    EC_PRIVATE_KEY,
    password=None,
    backend=default_backend()
)

def sign_request(method, path, body=""):
    timestamp = str(int(time.time()))
    prehash = f"{timestamp}{method.upper()}{path}{body}"
    signature = private_key.sign(prehash.encode(), ec.ECDSA(hashlib.sha256()))
    signature_b64 = base64.b64encode(signature).decode()
    headers = {
        "CB-ACCESS-KEY": API_KEY_ID,
        "CB-ACCESS-SIGN": signature_b64,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "CB-ACCESS-ORG-ID": ORG_ID,
        "Content-Type": "application/json"
    }
    return headers

def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        response = requests.post(url, data=data)
        logging.info(f"📬 Telegram response: {response.text}")
    except Exception as e:
        logging.error(f"Telegram error: {e}")

def get_latest_price(product_id):
    path = f"/api/v3/brokerage/products/{product_id}/ticker"
    url = urljoin(BASE_URL, path)
    headers = sign_request("GET", path)
    response = requests.get(url, headers=headers)
    return float(response.json().get("price", 0.0))

def place_market_order(product_id, side, notional):
    path = "/api/v3/brokerage/orders"
    url = urljoin(BASE_URL, path)
    body = {
        "client_order_id": f"order-{int(time.time())}",
        "product_id": product_id,
        "side": side,
        "order_configuration": {
            "market_market_ioc": {
                "quote_size": str(notional)
            }
        }
    }
    body_json = json.dumps(body)
    headers = sign_request("POST", path, body_json)
    response = requests.post(url, headers=headers, data=body_json)
    return response.json()

def run_bot():
    logging.info("🤖 Bot started.")
    try:
        current_price = get_latest_price(TRADING_PAIR)
        logging.info(f"💰 Current {TRADING_PAIR} price: ${current_price:.2f}")

        # Dummy Strategy: Always Buy (replace this logic)
        should_buy = True

        if should_buy:
            order = place_market_order(TRADING_PAIR, "BUY", MAX_TRADE_AMOUNT)
            logging.info(f"✅ Order placed: {order}")
            send_telegram_message(f"📈 Bought ${MAX_TRADE_AMOUNT} of {TRADING_PAIR} at ${current_price:.2f}")

            stop_price = current_price * (1 - STOP_LOSS_PCT)
            logging.info(f"🛡️ Stop-loss set at ${stop_price:.2f}")

            # Stop-loss monitor loop
            while True:
                time.sleep(30)
                new_price = get_latest_price(TRADING_PAIR)
                logging.info(f"📉 Checking stop-loss: Current ${new_price:.2f}")
                if new_price < stop_price:
                    sell_order = place_market_order(TRADING_PAIR, "SELL", MAX_TRADE_AMOUNT)
                    logging.warning(f"❗Stop-loss triggered! Sold at ${new_price:.2f}")
                    send_telegram_message(f"❗STOP-LOSS: Sold {TRADING_PAIR} at ${new_price:.2f}")
                    break
        else:
            logging.info("🛑 No buy signal. Holding.")

    except Exception as e:
        logging.error(f"🔥 Bot crashed: {e}")
        send_telegram_message(f"🔥 BOT ERROR: {e}")

if __name__ == "__main__":
    run_bot()
