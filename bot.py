import time
import ccxt
import os
import logging
import requests

logging.basicConfig(level=logging.INFO)

# === ENV VARIABLES ===
COINBASE_API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
COINBASE_PRIVATE_KEY = os.getenv("COINBASE_PRIVATE_KEY")
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", 200))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 0.05))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === EXCHANGE SETUP ===
exchange = ccxt.coinbase({
    'apiKey': COINBASE_API_KEY_ID,
    'secret': COINBASE_PRIVATE_KEY
})

symbol = 'BTC/USD'

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=data)
        if response.status_code != 200:
            logging.warning(f"⚠️ Telegram send failed: {response.text}")
    except Exception as e:
        logging.error(f"📵 Telegram error: {e}")

def fetch_safe_ohlcv(pair):
    retries = 5
    for i in range(retries):
        try:
            data = exchange.fetch_ohlcv(pair, timeframe='1m', limit=10)
            if not data or len(data) < 5:
                raise ValueError("Not enough data returned.")
            return data
        except Exception as e:
            logging.warning(f"[{i+1}/{retries}] Error fetching data: {e}")
            time.sleep(5)
    raise RuntimeError("Failed to fetch sufficient OHLCV data after retries.")

def run_bot():
    logging.info("🚀 Starting bot...")
    try:
        candles = fetch_safe_ohlcv(symbol)
        logging.info(f"✅ Got {len(candles)} candles")

        last_price = candles[-1][4]
        logging.info(f"💰 Last price of {symbol}: {last_price}")

        # === SMA STRATEGY ===
        closing_prices = [c[4] for c in candles]
        sma_short = sum(closing_prices[-3:]) / 3
        sma_long = sum(closing_prices) / len(closing_prices)

        logging.info(f"SMA short: {sma_short}, SMA long: {sma_long}")

        if sma_short > sma_long:
            amount = MAX_TRADE_AMOUNT / last_price
            logging.info(f"📈 Buying {amount:.6f} BTC at ${last_price:.2f}")
            order = exchange.create_market_buy_order(symbol, amount)
            logging.info(f"✅ Order placed: {order}")
            send_telegram_message(f"📈 TRADE ALERT: Bought {amount:.6f} BTC at ${last_price:.2f}")

            # Monitor for stop-loss
            entry_price = last_price
            stop_price = entry_price * (1 - STOP_LOSS_PCT)
            logging.info(f"🛡️ Stop-loss set at ${stop_price:.2f}")

            while True:
                current_price = exchange.fetch_ticker(symbol)['last']
                logging.info(f"📊 Current price: {current_price}")
                if current_price < stop_price:
                    sell_amount = order['amount']
                    logging.warning(f"⚠️ Stop-loss triggered! Selling {sell_amount} BTC")
                    sell_order = exchange.create_market_sell_order(symbol, sell_amount)
                    logging.info(f"✅ Sold at stop-loss: {sell_order}")
                    send_telegram_message(f"❗STOP-LOSS HIT: Sold {sell_amount} BTC at ${current_price:.2f}")
                    break
                time.sleep(30)  # Check every 30 seconds
        else:
            logging.info("🛑 No trade signal. Holding.")

    except Exception as e:
        logging.error(f"🔥 Bot failed: {e}")
        send_telegram_message(f"🔥 BOT ERROR: {e}")

if __name__ == "__main__":
    run_bot()
