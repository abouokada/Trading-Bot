# -*- coding: utf-8 -*-
import os
import sqlite3
import requests
import time
import logging
from datetime import datetime, timezone, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from binance.client import Client
from email.message import EmailMessage
import smtplib
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ تأكد من إعداد Telegram.")
    exit()
if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    print("❌ تأكد من إعداد Binance API.")
    exit()

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

conn = sqlite3.connect('trading_bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        symbol TEXT,
        side TEXT,
        quantity REAL,
        entry_price REAL,
        exit_price REAL,
        result TEXT,
        sentiment REAL
    )
''')
conn.commit()

DAILY_LOSS_LIMIT = -5.0
MAX_OPEN_TRADES = 2
open_trades = []
last_report_date = None
trade_executed_this_run = False
last_trade_date = None

TRAILING_STOP_PERCENT = 0.02
MAX_TRADE_DURATION = timedelta(minutes=30)
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT']

manual_mode = False
manual_symbol = ""
manual_side = "buy"
manual_quantity = 0.0

analyzer = SentimentIntensityAnalyzer()
last_update_id = None

def get_real_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        logging.error(f"⚠️ خطأ في جلب السعر لـ {symbol}: {e}")
        return 0.0

def analyze_sentiment(text):
    score = analyzer.polarity_scores(text)
    return score['compound']

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        logging.warning(f"⚠️ فشل إرسال Telegram: {e}")

def send_email_alert(subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        logging.warning(f"⚠️ فشل إرسال بريد إلكتروني: {e}")

def get_today_profit():
    today = datetime.now().date()
    cursor.execute("SELECT entry_price, exit_price, quantity, side, timestamp FROM trades")
    rows = cursor.fetchall()
    total = 0.0
    for entry, exit_price, qty, side, ts in rows:
        if datetime.fromisoformat(ts).date() == today:
            if side == "buy":
                total += (exit_price - entry) * qty
            else:
                total += (entry - exit_price) * qty
    return total

def is_valid_symbol(symbol):
    try:
        binance_client.get_symbol_ticker(symbol=symbol)
        return True
    except:
        return False

def choose_best_symbols():
    return [(symbol, analyze_sentiment(symbol)) for symbol in SYMBOLS]

def send_daily_report():
    send_telegram("📉 تم الوصول إلى حد الخسارة اليومية. تم إيقاف التداول مؤقتًا.")

def reset_daily_trade_flag():
    global trade_executed_this_run, last_trade_date
    today = datetime.now(timezone.utc).date()
    if last_trade_date != today:
        trade_executed_this_run = False
        last_trade_date = today

def execute_trades():
    global open_trades, trade_executed_this_run
    reset_daily_trade_flag()

    if trade_executed_this_run or len(open_trades) >= MAX_OPEN_TRADES:
        return

    if get_today_profit() <= DAILY_LOSS_LIMIT:
        send_email_alert("❌ خسارة يومية", "تجاوزت خسارة اليوم -5$")
        send_daily_report()
        return

    if manual_mode:
        if not is_valid_symbol(manual_symbol):
            print("⚠️ الرمز غير صالح")
            return
        sentiment = analyze_sentiment(f"Manual trade for {manual_symbol}")
        price = get_real_price(manual_symbol)
        trade = {
            'symbol': manual_symbol,
            'entry_price': price,
            'quantity': manual_quantity,
            'side': manual_side,
            'sentiment': sentiment,
            'highest_price': price,
            'start_time': datetime.now(timezone.utc)
        }
        open_trades.append(trade)
        trade_executed_this_run = True
        send_telegram(f"⚡ صفقة يدويًا على {manual_symbol} بسعر {price}")
        return

    for symbol, sentiment in choose_best_symbols():
        if len(open_trades) >= MAX_OPEN_TRADES:
            break
        price = get_real_price(symbol)
        qty = round(10 / price, 6)
        trade = {
            'symbol': symbol,
            'entry_price': price,
            'quantity': qty,
            'side': 'buy',
            'sentiment': sentiment,
            'highest_price': price,
            'start_time': datetime.now(timezone.utc)
        }
        open_trades.append(trade)
        trade_executed_this_run = True
        send_telegram(f"🚀 تم الدخول في صفقة {symbol} بسعر {price}")

def monitor_trades():
    global open_trades
    now = datetime.now(timezone.utc)
    updated = []

    for trade in open_trades:
        price = get_real_price(trade['symbol'])
        if price == 0:
            updated.append(trade)
            continue

        if price > trade['highest_price']:
            trade['highest_price'] = price

        stop_loss = trade['highest_price'] * (1 - TRAILING_STOP_PERCENT)
        reason = ""

        if price <= stop_loss:
            reason = "📉 تفعيل تريل ستوب"
        elif now - trade['start_time'] > MAX_TRADE_DURATION:
            reason = "⏰ انتهاء مدة الصفقة"

        if reason:
            profit = (price - trade['entry_price']) * trade['quantity']
            result = "ربح" if profit > 0 else "خسارة"
            send_telegram(f"✅ الخروج من {trade['symbol']} | {result} | {reason}")
            cursor.execute('''
                INSERT INTO trades (timestamp, symbol, side, quantity, entry_price, exit_price, result, sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now.isoformat(), trade['symbol'], trade['side'], trade['quantity'],
                trade['entry_price'], price, result, trade['sentiment']
            ))
            conn.commit()
        else:
            updated.append(trade)

    open_trades = updated

def handle_telegram_commands():
    global last_update_id, manual_mode, manual_symbol, manual_side, manual_quantity

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1} if last_update_id else {}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if "result" in data:
            for update in data["result"]:
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id", "")
                parts = text.strip().split()

                if text.startswith("/status"):
                    status = "📊 الصفقات المفتوحة:\n"
                    if not open_trades:
                        status += "لا توجد صفقات مفتوحة حاليًا."
                    else:
                        for t in open_trades:
                            status += f"- {t['symbol']} | الكمية: {t['quantity']} | السعر: {t['entry_price']}\n"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={"chat_id": chat_id, "text": status})

                elif text.startswith("/daily"):
                    profit = round(get_today_profit(), 2)
                    msg = f"📅 أرباح اليوم: {profit}$"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={"chat_id": chat_id, "text": msg})

                elif text.startswith("/manual") and len(parts) == 4:
                    symbol, side, qty = parts[1].upper(), parts[2].lower(), float(parts[3])
                    if not is_valid_symbol(symbol):
                        msg = f"❌ الرمز غير صالح: {symbol}"
                    else:
                        manual_mode = True
                        manual_symbol = symbol
                        manual_side = side
                        manual_quantity = qty
                        msg = f"✅ تم إعداد صفقة يدويًا: {symbol} | {side} | الكمية: {qty}"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={"chat_id": chat_id, "text": msg})

                elif text.startswith("/start"):
                    msg = "🤖 أهلاً بك! أوامر البوت:\n/status - الصفقات المفتوحة\n/daily - أرباح اليوم\n/manual BTCUSDT buy 0.01 - صفقة يدوية"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={"chat_id": chat_id, "text": msg})
    except Exception as e:
        logging.warning(f"⚠️ فشل أوامر Telegram: {e}")

if __name__ == '__main__':
    print("🤖 بدء تشغيل البوت...")
    print("⚙️ اختر وضع التشغيل:")
    print("1. 🤖 تداول تلقائي")
    print("2. ✍️ تداول يدوي")
    choice = input("🔢 رقم الوضع: ").strip()

    if choice == '2':
        manual_mode = True
        manual_symbol = input("💰 الرمز (مثل BTCUSDT): ").strip().upper()
        if not is_valid_symbol(manual_symbol):
            print("❌ الرمز غير صالح.")
            manual_mode = False
        else:
            manual_side = input("🧭 نوع الصفقة (buy/sell): ").strip().lower()
            manual_quantity = float(input("📊 الكمية: ").strip())

    while True:
        try:
            handle_telegram_commands()
            execute_trades()
            monitor_trades()
            now = datetime.now(timezone.utc)
            if now.hour == 23 and now.minute == 59 and last_report_date != now.date():
                send_daily_report()
                last_report_date = now.date()
            time.sleep(10)
        except KeyboardInterrupt:
            print("🛑 تم إيقاف البوت يدويًا.")
            break
        except Exception as e:
            logging.error(f"⚠️ خطأ غير متوقع: {e}")
            time.sleep(10)
