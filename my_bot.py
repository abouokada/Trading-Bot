import asyncio
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8099631365:AAFzJlZ6XNOeTUYg5mQsbxI4Fx9mT5BABCo"
CHAT_ID = 8186638235  # استبدلها بـ chat_id الخاص بك

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! هذا بوت تجريبي.\nأرسل /help للمساعدة."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هذه بعض الأوامر المتاحة:\n"
        "/start - بداية المحادثة\n"
        "/help - عرض المساعدة\n"
        "/ping - اختبار سرعة الرد"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong 🏓")

async def send_manual_message(app):
    # هذه رسالة تلقائية ترسلها عبر البوت لرقم دردشة معين (مثلاً تذكير)
    await app.bot.send_message(chat_id=CHAT_ID, text="هذه رسالة تلقائية من البوت!")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))

    # إعداد أوامر تظهر في واجهة تيليجرام مع البوت
    await app.bot.set_my_commands([
        BotCommand("start", "بدء المحادثة"),
        BotCommand("help", "عرض المساعدة"),
        BotCommand("ping", "اختبار سرعة الرد"),
    ])

    # تشغيل البوت (ينتظر الرسائل ويعالجها)
    # يمكنك إلغاء التعليق التالي لإرسال رسالة تلقائية عند بدء التشغيل
    # await send_manual_message(app)

    print("البوت شغال، اضغط Ctrl+C للخروج...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
