from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()
bot = Bot(os.getenv("TELEGRAM_TOKEN"))
chat_id = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(msg):
    try:
        bot.send_message(chat_id=chat_id, text=msg)
    except:
        print("[Telegram] Failed to send message")
