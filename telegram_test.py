import requests

TELEGRAM_TOKEN = "8099631365:AAFzJlZ6XNOeTUYg5mQsbxI4Fx9mT5BABCo"
TELEGRAM_CHAT_ID = "8186638235"

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": "✅ تم الاتصال بنجاح، هذه رسالة اختبار من بوت التداول!"
}
response = requests.post(url, data=payload)

if response.status_code == 200:
    print("✅ تم إرسال الرسالة بنجاح!")
else:
    print(f"❌ فشل في إرسال الرسالة، الكود: {response.status_code}")
    print("الرد الكامل من الخادم:")
    print(response.text)  # هذا يعرض محتوى الرد من Telegram API
