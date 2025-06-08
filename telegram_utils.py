
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{8099631365:AAFzJlZ6XNOeTUYg5mQsbxI4Fx9mT5BABCo}/sendMessage"
    payload = {
        "chat_id": 8186638235,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ تم إرسال رسالة Telegram.")
        else:
            print(f"❌ فشل إرسال Telegram - الكود: {response.status_code} | {response.text}")
    except Exception as e:
        print(f"⚠️ خطأ في إرسال Telegram: {e}")
