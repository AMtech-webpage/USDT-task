import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from telebot.apihelper import ApiTelegramException

# =====================================================================
# 1. CONFIGURATION & CONSTANTS
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8618388592:AAFRaEpzv9Ans816Thg0OF4p_DvrV1Y_j6w")
REQUIRED_CHANNEL = "@legitupdateontelegram"
ADMIN_PAYOUT_CHANNEL = "@USDTsettlemente"

MIN_WITHDRAWAL = 2.0
REF_REWARD = 0.2
PROMO_REWARD = 4.0 # Reward for using the MUIZ promo code

# Task configuration
YT_TASKS = [
    {"id": "yt_1", "title": "Watch YouTube Video 1", "url": "https://youtube.com/shorts/M4PF2V7TOqE", "reward": 0.1, "duration": 60},
    {"id": "yt_2", "title": "Watch YouTube Video 2", "url": "https://youtube.com/shorts/JfinwV1CFuc", "reward": 0.1, "duration": 60},
    {"id": "yt_3", "title": "Watch YouTube Video 3", "url": "https://youtube.com/shorts/sT93F-rFmzY", "reward": 0.1, "duration": 60}
]

APP_TASKS = [
    {"id": "app_1", "title": "Download & Use App 1", "url": "https://playbb.fun/u/28229500", "reward": 0.5, "duration": 120},
    {"id": "app_2", "title": "Download HiFami App", "url": "https://s.hifamiapp.com/1/b6xaDAoXh", "reward": 0.5, "duration": 120}
]

ALL_TASKS = YT_TASKS + APP_TASKS

bot = telebot.TeleBot(BOT_TOKEN)

# =====================================================================
# 2. DATABASE ENGINE
# =====================================================================
DB_NAME = "users.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0.0,
                wallet_address TEXT DEFAULT NULL,
                referred_by INTEGER DEFAULT NULL
            )
        """)
        
        # Safely add the used_promo column if it doesn't exist yet
        try:
            c.execute("ALTER TABLE users ADD COLUMN used_promo INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass # Column already exists

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_tasks (
                user_id INTEGER,
                task_id TEXT,
                start_time REAL,
                is_completed INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, task_id)
            )
        """)
        conn.commit()

def db_execute(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        return c.lastrowid

def db_fetch_one(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchone()

def db_fetch_all(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()

# =====================================================================
# 3. HTTP HEALTH SERVER
# =====================================================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is live and running.")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# =====================================================================
# 4. HELPER FUNCTIONS
# =====================================================================
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except ApiTelegramException:
        return False
    except Exception:
        return False

def show_verification_gate(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Join Official Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"))
    markup.add(InlineKeyboardButton("🔄 Verify Membership", callback_data="verify_membership"))
    
    bot.send_message(
        chat_id,
        "🔒 *Access Denied*\n\nYou must join our official channel to use this bot and start earning.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def show_dashboard(chat_id, user_id):
    user_data = db_fetch_one("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
    if not user_data:
        return
    
    balance, wallet = user_data
    wallet_display = wallet if wallet else "Not Set"

    text = (
        f"📊 *USER DASHBOARD*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Balance:* `${balance:.2f}`\n"
        f"💳 *Wallet:* `{wallet_display}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Select an option below:"
    )

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Tasks", callback_data="menu_tasks"),
        InlineKeyboardButton("💳 Withdraw", callback_data="menu_withdraw")
    )
    markup.add(
        InlineKeyboardButton("💼 Set Wallet", callback_data="menu_wallet"),
        InlineKeyboardButton("👥 Referral Link", callback_data="menu_referral")
    )
    # Added Promo Code Button
    markup.add(
        InlineKeyboardButton("🎁 Promo Code", callback_data="menu_promo")
    )

    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# =====================================================================
# 5. CORE ROUTERS & COMMANDS
# =====================================================================
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    args = message.text.split()
    ref_id = None

    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])

    user_exists = db_fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))

    if user_exists:
        if ref_id and ref_id != user_id:
            try:
                bot.send_message(ref_id, "❌ REFERRAL FAILED: User already exists")
            except ApiTelegramException:
                pass
    else:
        if ref_id == user_id:
            bot.send_message(chat_id, "❌ REFERRAL FAILED: You cannot refer yourself")
            db_execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        elif ref_id:
            referrer_exists = db_fetch_one("SELECT user_id FROM users WHERE user_id = ?", (ref_id,))
            if referrer_exists:
                db_execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
                db_execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REF_REWARD, ref_id))
                try:
                    bot.send_message(ref_id, f"🎉 *New Referral!* You earned `${REF_REWARD:.2f}`", parse_mode="Markdown")
                except ApiTelegramException:
                    pass
            else:
                db_execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        else:
            db_execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))

    if not check_channel_membership(user_id):
        show_verification_gate(chat_id)
    else:
        show_dashboard(chat_id, user_id)

# =====================================================================
# 6. CALLBACK QUERY HANDLERS (UI Navigation)
# =====================================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "verify_membership":
        if check_channel_membership(user_id):
            bot.answer_callback_query(call.id, "✅ Verification successful!")
            bot.delete_message(chat_id, call.message.message_id)
            show_dashboard(chat_id, user_id)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)
        return

    if not check_channel_membership(user_id):
        bot.answer_callback_query(call.id, "❌ You must join the channel first!", show_alert=True)
        return

    if call.data == "menu_main":
        bot.delete_message(chat_id, call.message.message_id)
        show_dashboard(chat_id, user_id)

    elif call.data == "menu_referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        text = (
            f"👥 *REFERRAL PROGRAM*\n\n"
            f"Share your link with friends. When they join, you earn *${REF_REWARD:.2f}* instantly!\n\n"
            f"🔗 *Your Link:* `{ref_link}`"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "menu_wallet":
        # UPDATED: Added recommendation for Trust Wallet
        text = (
            "💼 *WALLET SETUP*\n\n"
            "Please reply to this message with your USDT wallet address.\n\n"
            "💡 *Tip:* We highly recommend using *Trust Wallet* to receive your funds safely and quickly."
        )
        msg = bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_wallet_input)

    elif call.data == "menu_promo":
        text = "🎁 *PROMO CODE*\n\nPlease reply to this message with your promo code to claim free rewards!"
        msg = bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_promo_input)

    elif call.data == "menu_withdraw":
        user_data = db_fetch_one("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
        if not user_data:
            return
        
        balance, wallet = user_data
        
        if not wallet or len(wallet.strip()) < 10:
            bot.answer_callback_query(call.id, "❌ You must set a valid wallet address first!", show_alert=True)
            return
            
        if balance < MIN_WITHDRAWAL:
            bot.answer_callback_query(call.id, f"❌ Minimum withdrawal is ${MIN_WITHDRAWAL:.2f}", show_alert=True)
            return

        db_execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
        
        # UPDATED: Gather extended user info for the admin notification
        user_info = call.from_user
        first_name = user_info.first_name if user_info.first_name else ""
        last_name = user_info.last_name if user_info.last_name else ""
        full_name = f"{first_name} {last_name}".strip()
        username = f"@{user_info.username}" if user_info.username else "No Username"

        admin_req = (
            f"⚡ *NEW WITHDRAWAL REQUEST*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Name:* `{full_name}`\n"
            f"🔗 *Username:* {username}\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"💰 *Amount:* `${balance:.2f}`\n"
            f"💳 *Wallet:* `{wallet}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        try:
            bot.send_message(ADMIN_PAYOUT_CHANNEL, admin_req, parse_mode="Markdown")
        except ApiTelegramException as e:
            print(f"Failed to notify admin channel: {e}")

        bot.edit_message_text(
            "✅ *WITHDRAWAL REQUESTED*\n\nYour request has been submitted to the administration for processing.",
            chat_id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        time.sleep(3)
        show_dashboard(chat_id, user_id)

    elif call.data == "menu_tasks":
        markup = InlineKeyboardMarkup(row_width=1)
        
        for task in ALL_TASKS:
            task_state = db_fetch_one("SELECT is_completed FROM user_tasks WHERE user_id = ? AND task_id = ?", (user_id, task["id"]))
            
            if task_state and task_state[0] == 1:
                btn_text = f"✅ {task['title']} (Completed)"
                markup.add(InlineKeyboardButton(btn_text, callback_data="ignore"))
            else:
                btn_text = f"▶️ {task['title']} (${task['reward']:.2f})"
                markup.add(InlineKeyboardButton(btn_text, callback_data=f"task_start_{task['id']}"))
                
        markup.add(InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
        bot.edit_message_text("📋 *AVAILABLE TASKS*\n\nSelect a task below to start earning:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("task_start_"):
        task_id = call.data.replace("task_start_", "")
        task = next((t for t in ALL_TASKS if t["id"] == task_id), None)
        
        if not task:
            return

        current_time = time.time()
        db_execute("""
            INSERT INTO user_tasks (user_id, task_id, start_time, is_completed) 
            VALUES (?, ?, ?, 0) 
            ON CONFLICT(user_id, task_id) 
            DO UPDATE SET start_time = excluded.start_time WHERE is_completed = 0
        """, (user_id, task_id, current_time))

        text = (
            f"🎬 *TASK IN PROGRESS*\n\n"
            f"*{task['title']}*\n"
            f"Reward: `${task['reward']:.2f}`\n\n"
            f"1. Click the button below to open the link.\n"
            f"2. Complete the objective (requires approx {task['duration']} seconds).\n"
            f"3. Return here and click Verify."
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 Open Link", url=task["url"]))
        markup.add(InlineKeyboardButton("🔄 Verify Task", callback_data=f"task_verify_{task_id}"))
        markup.add(InlineKeyboardButton("⬅️ Cancel", callback_data="menu_tasks"))
        
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("task_verify_"):
        task_id = call.data.replace("task_verify_", "")
        task = next((t for t in ALL_TASKS if t["id"] == task_id), None)
        
        if not task:
            return

        task_record = db_fetch_one("SELECT start_time, is_completed FROM user_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        
        if not task_record:
            bot.answer_callback_query(call.id, "❌ Task session not found. Please restart the task.", show_alert=True)
            return
            
        start_time, is_completed = task_record
        
        if is_completed == 1:
            bot.answer_callback_query(call.id, "❌ You have already been rewarded for this task.", show_alert=True)
            return
            
        elapsed_time = time.time() - start_time
        if elapsed_time < task["duration"]:
            remaining = int(task["duration"] - elapsed_time)
            bot.answer_callback_query(call.id, f"⚠️ Verification Pending: Please wait {remaining} more seconds.", show_alert=True)
            return

        db_execute("UPDATE user_tasks SET is_completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        db_execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (task["reward"], user_id))
        
        bot.answer_callback_query(call.id, f"🎉 Success! +${task['reward']:.2f} added to balance.", show_alert=True)
        bot.delete_message(chat_id, call.message.message_id)
        show_dashboard(chat_id, user_id)

    elif call.data == "ignore":
        bot.answer_callback_query(call.id, "Task already completed.")

# =====================================================================
# 7. CHAT INPUT HANDLERS (Wallet & Promo Code)
# =====================================================================
def process_wallet_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    wallet_address = message.text.strip() if message.text else ""

    if len(wallet_address) < 10:
        bot.send_message(chat_id, "❌ *Invalid Wallet Address*\nAddress is too short. Try setting it again.", parse_mode="Markdown")
        time.sleep(2)
        show_dashboard(chat_id, user_id)
        return

    db_execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet_address, user_id))
    bot.send_message(chat_id, f"✅ *Wallet Updated Successfully*\n`{wallet_address}`", parse_mode="Markdown")
    time.sleep(1)
    show_dashboard(chat_id, user_id)

def process_promo_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    promo_input = message.text.strip().lower() if message.text else ""

    if promo_input == "muiz":
        # Check if the user has already used a promo code
        user_data = db_fetch_one("SELECT used_promo FROM users WHERE user_id = ?", (user_id,))
        
        if user_data and user_data[0] == 1:
            bot.send_message(chat_id, "❌ You have already claimed this promo code!", parse_mode="Markdown")
        else:
            # Add reward and mark promo as used
            db_execute("UPDATE users SET balance = balance + ?, used_promo = 1 WHERE user_id = ?", (PROMO_REWARD, user_id))
            bot.send_message(chat_id, f"🎉 *Promo Code Accepted!*\n\nYou claimed the 'MUIZ' code and earned `${PROMO_REWARD:.2f}`!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ *Invalid Promo Code*\nThis code does not exist or has expired.", parse_mode="Markdown")
        
    time.sleep(2)
    show_dashboard(chat_id, user_id)

# =====================================================================
# 8. INITIALIZATION & MAIN LOOP
# =====================================================================
if __name__ == "__main__":
    print("Initializing Database...")
    init_db()
    
    print("Starting Render Health Server Thread...")
    threading.Thread(target=run_health_server, daemon=True).start()
    
    print("Starting Telegram Bot Polling Engine...")
    bot.infinity_polling(skip_pending=True)
