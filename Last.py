import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
BOT_TOKEN = "8366284497:AAGqy2V6Mh5HI_GmNn15kh_bm0-x2BzplQw"
ADMIN_GROUP_CHAT_ID = "@USDTsettlemente"
MIN_WITHDRAWAL = 2.0
PROMO_REWARD = 2.00

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            wallet_address TEXT DEFAULT NULL,
            promo_used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user_data(user_id):
    """Safely retrieves data; returns defaults if user not found."""
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("SELECT balance, wallet_address, promo_used FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = (0.0, None, 0)
    conn.close()
    return row

# --- RENDER KEEPALIVE ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_server():
    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), HealthCheck)
    server.serve_forever()

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def start(message):
    balance, _, _ = get_user_data(message.chat.id)
    text = f"💰 *Account Balance:* `${balance:.2f} USD`\n\nWelcome to the Earning Hub!"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📺 Watch Video ($0.10)", callback_data="task_yt"))
    markup.add(InlineKeyboardButton("💳 Withdraw Funds", callback_data="withdraw"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.message.chat.id
    
    if call.data == "task_yt":
        # Simulate video task
        conn = sqlite3.connect("earning_platform.db")
        conn.execute("UPDATE users SET balance = balance + 0.10 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "+$0.10 earned!")
        
    elif call.data == "withdraw":
        balance, wallet, _ = get_user_data(user_id)
        if not wallet:
            # Fixed Syntax: only one reply_markup per call
            bot.send_message(user_id, "❌ Please set your wallet first using /setwallet.")
        elif balance < MIN_WITHDRAWAL:
            bot.send_message(user_id, f"❌ Min withdrawal is ${MIN_WITHDRAWAL:.2f}")
        else:
            bot.send_message(ADMIN_GROUP_CHAT_ID, f"Payout: User {user_id} wants ${balance:.2f} to {wallet}")
            conn = sqlite3.connect("earning_platform.db")
            conn.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "Withdrawal submitted!")

@bot.message_handler(commands=['setwallet'])
def ask_wallet(message):
    msg = bot.send_message(message.chat.id, "Reply with your USDT address:")
    bot.register_next_step_handler(msg, save_wallet)

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
    # Use interval polling to prevent 409 conflict
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
