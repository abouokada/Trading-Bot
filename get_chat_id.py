from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8099631365:AAFzJlZ6XNOeTUYg5mQsbxI4Fx9mT5BABCo"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ تم استلام الرسالة! chat_id: {chat_id}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 البوت يعمل. أرسل له أي رسالة من تليجرام لمعرفة chat_id...")
app.run_polling()
