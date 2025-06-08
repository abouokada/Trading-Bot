from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = '8099631365:AAFzJlZ6XNOeTUYg5mQsbxI4Fx9mT5BABCo'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('أهلًا! كيف يمكنني مساعدتك؟')

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("✅ بوت التداول شغّال! جاهز للعمل 💹")
    app.run_polling()
