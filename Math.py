import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from telebot.apihelper import ApiTelegramException

# =====================================================================
# 1. CONFIGURATION
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8618388592:AAFRaEpzv9Ans816Thg0OF4p_DvrV1Y_j6w")
# Now treated as a user account for follow/interaction
FOLLOW_ACCOUNT = "legitupdateontelegram" 
ADMIN_PAYOUT_CHANNEL = "@USDTsettlemente"

MIN_WITHDRAWAL = 2.0
REF_REWARD = 0.2
PROMO_REWARD = 0.50

# Tasks with new Subscriptions
ALL_TASKS = [
    {"id": "yt_sub", "title": "Subscribe to YouTube", "url": "https://youtube.com/@legitupdateontelegram", "reward": 0.2, "duration": 10},
    {"id": "wa_join", "title": "Join WhatsApp Channel", "url": "https://whatsapp.com/channel/your_link_here", "reward": 0.2, "duration": 10},
    {"id": "yt_1", "title": "Watch Short 1", "url": "https://youtube.com/shorts/M4PF2V7TOqE", "reward": 0.1, "duration": 60}
]

bot = telebot.TeleBot(BOT_TOKEN)
DB_NAME = "users.db"

# =====================================================================
# 2. DATABASE & SERVER
# =====================================================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, wallet_address TEXT, referred_by INTEGER, used_promo INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS user_tasks (user_id INTEGER, task_id TEXT, start_time REAL, is_completed INTEGER DEFAULT 0, PRIMARY KEY (user_id, task_id))")
        conn.commit()

def db_execute(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

def db_fetch_one(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchone()

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive.")

def run_health_server():
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), HealthCheckHandler).serve_forever()

# =====================================================================
# 3. INTERFACE
# =====================================================================
def show_dashboard(chat_id, user_id):
    user_data = db_fetch_one("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
    balance, wallet = user_data
    text = f"📊 *DASHBOARD*\n💰 Balance: `${balance:.2f}`\n💳 Wallet: `{wallet if wallet else 'Not Set'}`"
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Tasks", callback_data="menu_tasks"),
        InlineKeyboardButton("💳 Withdraw", callback_data="menu_withdraw"),
        InlineKeyboardButton("💼 Set Wallet", callback_data="menu_wallet"),
        InlineKeyboardButton("🎁 Promo", callback_data="menu_promo")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# =====================================================================
# 4. CALLBACKS
# =====================================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if call.data == "menu_tasks":
        markup = InlineKeyboardMarkup(row_width=1)
        for task in ALL_TASKS:
            status = db_fetch_one("SELECT is_completed FROM user_tasks WHERE user_id = ? AND task_id = ?", (user_id, task["id"]))
            if status and status[0] == 1:
                markup.add(InlineKeyboardButton(f"✅ {task['title']}", callback_data="ignore"))
            else:
                markup.add(InlineKeyboardButton(f"▶️ {task['title']}", callback_data=f"task_start_{task['id']}"))
        markup.add(InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
        bot.edit_message_text("📋 Select task to earn:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "menu_withdraw":
        user_data = db_fetch_one("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
        if user_data[0] < MIN_WITHDRAWAL:
            bot.answer_callback_query(call.id, f"Min withdrawal is ${MIN_WITHDRAWAL}")
            return
        
        # Admin Notification
        full_name = f"{call.from_user.first_name} {call.from_user.last_name or ''}"
        msg = f"⚡ *New Withdrawal*\n👤 Name: {full_name}\n🆔 ID: `{user_id}`\n💰 Amount: `${user_data[0]}`\n💳 Wallet: `{user_data[1]}`"
        bot.send_message(ADMIN_PAYOUT_CHANNEL, msg, parse_mode="Markdown")
        db_execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "Withdrawal request sent!")
        show_dashboard(chat_id, user_id)

    elif call.data.startswith("task_start_"):
        task_id = call.data.replace("task_start_", "")
        task = next((t for t in ALL_TASKS if t["id"] == task_id), None)
        db_execute("INSERT OR IGNORE INTO user_tasks (user_id, task_id, start_time) VALUES (?, ?, ?)", (user_id, task_id, time.time()))
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 Open Link", url=task["url"]), InlineKeyboardButton("✅ Verify", callback_data=f"task_verify_{task_id}"))
        bot.edit_message_text(f"Click the link and complete the task:\n{task['url']}", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("task_verify_"):
        task_id = call.data.replace("task_verify_", "")
        task = next((t for t in ALL_TASKS if t["id"] == task_id), None)
        db_execute("UPDATE user_tasks SET is_completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        db_execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (task["reward"], user_id))
        bot.answer_callback_query(call.id, "Reward added!")
        show_dashboard(chat_id, user_id)

# =====================================================================
# 5. INITIALIZATION
# =====================================================================
if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_health_server, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
