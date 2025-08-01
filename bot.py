
import time
import ccxt
import os
import logging

logging.basicConfig(level=logging.INFO)

# Get credentials from environment variables
COINBASE_API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
COINBASE_PRIVATE_KEY = os.getenv("COINBASE_PRIVATE_KEY")
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", 200))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 0.05))

# Setup exchange
exchange = ccxt.coinbase({
    'apiKey': COINBASE_API_KEY_ID,
    'secret': COINBASE_PRIVATE_KEY
})

# Pick pair
symbol = 'BTC/USD'

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

        # Example trading logic (replace with your actual strategy)
        last_price = candles[-1][4]
        logging.info(f"💰 Last price of {symbol}: {last_price}")
        # ... trading logic ...
    except Exception as e:
        logging.error(f"🔥 Bot failed: {e}")

if __name__ == "__main__":
    run_bot()
