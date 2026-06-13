import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
BOT_TOKEN = "8366284497:AAGqy2V6Mh5HI_GmNn15kh_bm0-x2BzplQw"
TG_CHANNEL = "@legitupdateontelegram"
ADMIN_GROUP_CHAT_ID = "@USDTsettlemente"
MIN_WITHDRAWAL = 2.0
REFERRAL_REWARD = 0.2
PROMO_REWARD = 2.00

bot = telebot.TeleBot(BOT_TOKEN)
user_watch_tracker = {}

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            wallet_address TEXT DEFAULT NULL,
            promo_used INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("SELECT balance, wallet_address, promo_used FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = (0.0, None, 0)
    conn.close()
    return row # (balance, wallet, promo_used)

# --- WEB SERVER (For Render keep-alive) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), HealthCheck)
    server.serve_forever()

# --- BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    balance, wallet, _ = get_user(message.chat.id)
    wallet_txt = wallet if wallet else "Not Set"
    text = f"💰 Balance: ${balance:.2f}\n💳 Wallet: {wallet_txt}\n\nWelcome! Use the menu to earn."
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"))
    markup.add(InlineKeyboardButton("⚙️ Set Wallet", callback_data="set_wallet"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "set_wallet":
        msg = bot.send_message(call.message.chat.id, "Please reply with your USDT address:")
        bot.register_next_step_handler(msg, save_wallet)
    elif call.data == "withdraw":
        balance, wallet, _ = get_user(call.message.chat.id)
        if not wallet:
            bot.answer_callback_query(call.id, "Set your wallet first!")
        elif balance < MIN_WITHDRAWAL:
            bot.answer_callback_query(call.id, f"Min withdrawal is ${MIN_WITHDRAWAL}")
        else:
            bot.send_message(ADMIN_GROUP_CHAT_ID, f"Payout Request: User {call.message.chat.id} wants ${balance} to {wallet}")
            conn = sqlite3.connect("earning_platform.db")
            conn.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (call.message.chat.id,))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "Withdrawal request sent!")

def save_wallet(message):
    addr = message.text.strip()
    conn = sqlite3.connect("earning_platform.db")
    conn.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (addr, message.chat.id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Wallet updated!")

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_server, daemon=True).start()
    bot.infinity_polling()
