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

symbol = 'ETH/USD'

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
            logging.info(f"📈 Buying ${MAX_TRADE_AMOUNT:.2f} worth of {symbol}")
            order = exchange.create_order(symbol, 'market', 'buy', None, {'cost': MAX_TRADE_AMOUNT})
            logging.info(f"✅ Order placed: {order}")
            send_telegram_message(f"📈 TRADE ALERT: Bought ${MAX_TRADE_AMOUNT:.2f} of {symbol} at ${last_price:.2f}")

            # Monitor for stop-loss
            entry_price = last_price
            stop_price = entry_price * (1 - STOP_LOSS_PCT)
            logging.info(f"🛡️ Stop-loss set at ${stop_price:.2f}")

            while True:
                current_price = exchange.fetch_ticker(symbol)['last']
                logging.info(f"📊 Current price: {current_price}")
                if current_price < stop_price:
                    amount_to_sell = order['info'].get('filled_size') or order.get('amount', 0)
                    logging.warning(f"⚠️ Stop-loss triggered! Selling {amount_to_sell} ETH")
                    sell_order = exchange.create_order(symbol, 'market', 'sell', amount_to_sell)
                    logging.info(f"✅ Sold at stop-loss: {sell_order}")
                    send_telegram_message(f"❗STOP-LOSS HIT: Sold {amount_to_sell} ETH at ${current_price:.2f}")
                    break
                time.sleep(30)  # Check every 30 seconds
        else:
            logging.info("🛑 No trade signal. Holding.")

    except Exception as e:
        logging.error(f"🔥 Bot failed: {e}")
        send_telegram_message(f"🔥 BOT ERROR: {e}")

if __name__ == "__main__":
    run_bot()
