import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = "8366284497:AAGqy2V6Mh5HI_GmNn15kh_bm0-x2BzplQw"
bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE SAFETY ---
def init_db():
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, wallet_address TEXT)")
    conn.commit()
    conn.close()

def get_wallet(user_id):
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("SELECT wallet_address FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    # If user doesn't exist or wallet is NULL, return None
    return res[0] if res and res[0] else None

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def start(message):
    # Ensure user exists in DB
    conn = sqlite3.connect("earning_platform.db")
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.chat.id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Bot is ready! Use the menu.")

@bot.callback_query_handler(func=lambda call: call.data == "ui_withdraw")
def withdraw(call):
    wallet = get_wallet(call.message.chat.id)
    if not wallet:
        bot.answer_callback_query(call.id, "❌ Link a wallet first!")
        return
    bot.answer_callback_query(call.id, "Withdrawal processed!")

# --- RENDER KEEPALIVE ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), HealthCheck)
    server.serve_forever()

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_server, daemon=True).start()
    bot.infinity_polling()
