import asyncio
from telegram import Bot

TOKEN = "8099631365:AAFzJlZ6XNOeTUYg5mQsbxI4Fx9mT5BABCo"
CHAT_ID = 8186638235  # رقم الشات آي دي الصحيح

async def send_telegram_message(text):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text)
    print("تم إرسال الرسالة!")

if __name__ == "__main__":
    asyncio.run(send_telegram_message("✅ الرسالة وصلت بنجاح! 🚀"))
