
import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
# Updated with your new revoked token
BOT_TOKEN = "8366284497:AAHPIq52by3eYTLF5OY_47VFK_SGEYa7wj8-"
ADMIN_GROUP = "@USDTsettlemente"
MIN_WITHDRAWAL = 2.0

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    # Fixed schema to ensure 'wallet' column exists
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, wallet TEXT)")
    conn.commit()
    conn.close()

def get_user_row(user_id):
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    # Always ensure a row exists so fetchone() never returns None
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    c.execute("SELECT balance, wallet FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# --- RENDER KEEPALIVE ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), HealthCheck)
    server.serve_forever()

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def start(message):
    balance, wallet = get_user_row(message.chat.id)
    text = f"💰 Balance: ${balance:.2f}\n💳 Wallet: {wallet if wallet else 'Not Set'}"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"))
    markup.add(InlineKeyboardButton("⚙️ Set Wallet", callback_data="set"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "set":
        msg = bot.send_message(call.message.chat.id, "Reply with your USDT address:")
        bot.register_next_step_handler(msg, save_wallet)
    elif call.data == "withdraw":
        balance, wallet = get_user_row(call.message.chat.id)
        if not wallet:
            bot.answer_callback_query(call.id, "❌ Set wallet first!")
        elif balance < MIN_WITHDRAWAL:
            bot.answer_callback_query(call.id, f"Min: ${MIN_WITHDRAWAL}")
        else:
            bot.send_message(ADMIN_GROUP, f"Payout: {call.message.chat.id} needs ${balance}")
            conn = sqlite3.connect("earning_platform.db")
            conn.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (call.message.chat.id,))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "Request sent!")

def save_wallet(message):
    conn = sqlite3.connect("earning_platform.db")
    conn.execute("UPDATE users SET wallet = ? WHERE user_id = ?", (message.text.strip(), message.chat.id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Wallet saved!")

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_server, daemon=True).start()
    bot.infinity_polling()
