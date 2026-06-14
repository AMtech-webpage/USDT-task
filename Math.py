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
# Updated with your new token
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8618388592:AAFRaEpzv9Ans816Thg0OF4p_DvrV1Y_j6w")
REQUIRED_CHANNEL = "@legitupdateontelegram"
ADMIN_PAYOUT_CHANNEL = "@USDTsettlemente"

MIN_WITHDRAWAL = 2.0
REF_REWARD = 0.2

# Task configuration: times are in seconds
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
# 2. DATABASE ENGINE (Thread-Safe Context Manager)
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
# 3. HTTP HEALTH SERVER (For Render)
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
    """Verifies if the user is in the required channel."""
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except ApiTelegramException:
        # Bot might not be admin in the channel or user hasn't started the bot properly
        return False
    except Exception:
        return False

def show_verification_gate(chat_id):
    """Displays the mandatory channel join prompt."""
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
    """Renders the main user dashboard UI."""
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

    # Check if user exists safely
    user_exists = db_fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))

    if user_exists:
        if ref_id and ref_id != user_id:
            try:
                bot.send_message(ref_id, "❌ REFERRAL FAILED: User already exists")
            except ApiTelegramException:
                pass # Referrer might have blocked the bot
    else:
        # Process new user registration
        if ref_id == user_id:
            bot.send_message(chat_id, "❌ REFERRAL FAILED: You cannot refer yourself")
            db_execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        elif ref_id:
            # Verify referrer exists
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

    # Channel verification gate
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

    # 1. Membership Verification
    if call.data == "verify_membership":
        if check_channel_membership(user_id):
            bot.answer_callback_query(call.id, "✅ Verification successful!")
            bot.delete_message(chat_id, call.message.message_id)
            show_dashboard(chat_id, user_id)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)
        return

    # Security check: Must be verified for all other actions
    if not check_channel_membership(user_id):
        bot.answer_callback_query(call.id, "❌ You must join the channel first!", show_alert=True)
        return

    # 2. Main Menu Routing
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
        text = "💼 *WALLET SETUP*\n\nPlease reply to this message with your USDT wallet address."
        msg = bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_wallet_input)

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

        # Process Withdrawal
        db_execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
        
        admin_req = (
            f"⚡ *NEW WITHDRAWAL REQUEST*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User ID:* `{user_id}`\n"
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
        # Return to dashboard after 3 seconds
        time.sleep(3)
        show_dashboard(chat_id, user_id)

    # 3. Tasks Menu
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

    # 4. Task Execution Engine
    elif call.data.startswith("task_start_"):
        task_id = call.data.replace("task_start_", "")
        task = next((t for t in ALL_TASKS if t["id"] == task_id), None)
        
        if not task:
            return

        # Record start time
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
            bot.answer_callback_query(call.id, f"⚠️ Verification Pending: Please wait {remaining} more seconds and ensure you completed the action.", show_alert=True)
            return

        # Verification successful: Update records and reward user
        db_execute("UPDATE user_tasks SET is_completed = 1 WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        db_execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (task["reward"], user_id))
        
        bot.answer_callback_query(call.id, f"🎉 Success! +${task['reward']:.2f} added to balance.", show_alert=True)
        
        # Route back to tasks menu implicitly via code repetition or calling the main handler
        bot.delete_message(chat_id, call.message.message_id)
        show_dashboard(chat_id, user_id)

    elif call.data == "ignore":
        bot.answer_callback_query(call.id, "Task already completed.")

# =====================================================================
# 7. WALLET INPUT STATE HANDLER
# =====================================================================
def process_wallet_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    wallet_address = message.text.strip() if message.text else ""

    # Check for empty or invalid length (common for crypto wallets)
    if len(wallet_address) < 10:
        msg = bot.send_message(chat_id, "❌ *Invalid Wallet Address*\nAddress is too short or empty. Please try setting it again from the dashboard.", parse_mode="Markdown")
        time.sleep(2)
        show_dashboard(chat_id, user_id)
        return

    # Update database
    db_execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet_address, user_id))
    
    bot.send_message(chat_id, f"✅ *Wallet Updated Successfully*\n`{wallet_address}`", parse_mode="Markdown")
    time.sleep(1)
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
    # Using skip_pending=True to prevent flood of old requests on restart causing Error 409 conflicts
    bot.infinity_polling(skip_pending=True)
