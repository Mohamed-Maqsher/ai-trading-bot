from dotenv import load_dotenv
import os
import time
import schedule
import threading
import subprocess
from telegram_alerts import send_alert
from ml_predict import predict_next_move
from lstm_predict import predict_lstm

load_dotenv()

def trade_stock():
    move = predict_next_move()
    if move == 1:
        print("[AI BUY] AAPL is predicted to go UP")
        send_alert("🟢 BUY SIGNAL: AAPL predicted to go UP")
    elif move == 0:
        print("[AI SELL] AAPL is predicted to go DOWN")
        send_alert("🔴 SELL SIGNAL: AAPL predicted to go DOWN")
    else:
        print("[AI] Not enough data yet")

def trade_crypto():
    move = predict_lstm()
    if move > 0.5:
        print("[LSTM BUY] AAPL deep model predicts UP")
        send_alert("💹 LSTM BUY: AAPL trending upward")
    else:
        print("[LSTM SELL] AAPL deep model predicts DOWN")
        send_alert("📉 LSTM SELL: AAPL trending downward")

def retrain_model():
    subprocess.run(["python3", "ml_train.py"])
    subprocess.run(["python3", "lstm_train.py"])

schedule.every().day.at("09:00").do(retrain_model)

def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=schedule_thread, daemon=True).start()

while True:
    print("---- Running Trading Logic ----")
    trade_stock()
    trade_crypto()
    time.sleep(60)
