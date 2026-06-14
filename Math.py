import os
import psycopg2
import telebot
from telebot import types

# Load variables from Render Environment configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID") 

# 💰 REFERRAL CONFIGURATION METRICS
REFERRAL_REWARD = 0.30  

# 📋 ALL AVAILABLE MICRO-TASKS CONFIGURATION
# You can easily add, change, or remove apps and videos here!
TASKS = {
    "video_1": {"text": "📺 Watch YouTube Video Task 1", "reward": 0.50},
    "video_2": {"text": "📺 Watch YouTube Video Task 2", "reward": 0.50},
    "app_1": {"text": "📱 Download & Open Crypto App", "reward": 1.00},
    "app_2": {"text": "📱 Install & Register Gaming App", "reward": 1.50},
    "twitter": {"text": "🐦 Follow Twitter Sponsor", "reward": 0.50},
}

# ✅ Real verified Telegram community chat IDs
CHANNELS_TO_CHECK = [
    -1004478317088,  # Channel ID
    -1003639586815   # Group ID
]

# ✅ Community URL destinations
TG_LINK_1 = "https://t.me/+UkdkPcVoAMU2YTM0"
TG_GROUP_LINK = "https://t.me/legitupdateontelegram" 
WHATSAPP_LINK = "https://chat.whatsapp.com/EZgSS4NS4vKB6Uqtx1NiTH"
YOUTUBE_LINK = "https://youtube.com/beaconofislam"
TRUST_WALLET_URL = "https://trustwallet.com/download"

bot = telebot.TeleBot(BOT_TOKEN)

# --- Database Helper Functions ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def is_user_exist(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE telegram_id = %s;", (user_id,))
                return cur.fetchone() is not None
    except Exception as e:
        print(f"Error checking user existence: {e}")
        return False

def register_user(user_id, username):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (telegram_id, username, balance)
                    VALUES (%s, %s, 0.0000)
                    ON CONFLICT (telegram_id) DO UPDATE 
                    SET username = EXCLUDED.username;
                    """,
                    (user_id, username)
                )
                conn.commit()
    except Exception as e:
        print(f"Database registration error: {e}")

def get_user_data(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT balance, wallet_address FROM users WHERE telegram_id = %s;", (user_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"Database read error: {e}")
        return None

def update_wallet(user_id, wallet):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET wallet_address = %s WHERE telegram_id = %s;", (wallet, user_id))
                conn.commit()
    except Exception as e:
        print(f"Database wallet update error: {e}")

def update_balance(user_id, new_balance):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET balance = %s WHERE telegram_id = %s;", (new_balance, user_id))
                conn.commit()
    except Exception as e:
        print(f"Database balance setting error: {e}")

# --- Task & Bonus Core Tracking Engine ---
def is_item_claimed(user_id, item_name):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM completed_tasks WHERE telegram_id = %s AND task_name = %s;", 
                    (user_id, item_name)
                )
                return cur.fetchone() is not None
    except Exception as e:
        print(f"Error checking item status: {e}")
        return False

def award_item(user_id, item_name, reward_amount):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO completed_tasks (telegram_id, task_name) VALUES (%s, %s);", 
                    (user_id, item_name)
                )
                cur.execute(
                    "UPDATE users SET balance = balance + %s WHERE telegram_id = %s;", 
                    (reward_amount, user_id)
                )
                conn.commit()
                return True
    except Exception as e:
        print(f"Error executing reward transaction: {e}")
        return False

def get_referral_count(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM completed_tasks WHERE telegram_id = %s AND task_name LIKE 'referral_%%';", 
                    (user_id,)
                )
                res = cur.fetchone()
                return res[0] if res else 0
    except Exception as e:
        print(f"Error counting referrals: {e}")
        return 0


# --- STRICT VERIFICATION GATE CHECK ---
def check_compulsory_join(user_id):
    try:
        for chat_id in CHANNELS_TO_CHECK:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        print(f"Gate security block triggered: {e}")
        return False  # Strict enforcement: Always deny access if verification fails or database errors out

def send_verification_gate(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 1. Join Telegram Channel", url=TG_LINK_1),
        types.InlineKeyboardButton("💬 2. Join Telegram Group", url=TG_GROUP_LINK),
        types.InlineKeyboardButton("💬 3. Join WhatsApp Group", url=WHATSAPP_LINK),
        types.InlineKeyboardButton("📺 4. Subscribe on YouTube", url=YOUTUBE_LINK),
        types.InlineKeyboardButton("🔄 Verify Memberships", callback_data="verify_links")
    )
    text = (
        "⚠️ *Access Denied - Verification Required!*\n\n"
        "To protect our ecosystem, you must complete our compulsory community gates:\n\n"
        "1️⃣ Join our Telegram Channel\n"
        "2️⃣ Join our Telegram Group\n"
        "3️⃣ Join our WhatsApp Group\n"
        "4️⃣ Subscribe to our YouTube channel\n\n"
        "Once completed, click the verification button below to unlock your rewards panel!"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


# --- Persistent Reply Menu Generator ---
def send_main_menu(chat_id, text="Main Dashboard Loaded! Choose an option below to start earning:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📋 Tasks"),
        types.KeyboardButton("👥 Referrals"),  
        types.KeyboardButton("🎁 Bonus Code"),
        types.KeyboardButton("💼 Wallet Setup"),
        types.KeyboardButton("💵 Withdraw Status"),
        types.KeyboardButton("📊 Balance")
    )
    bot.send_message(chat_id, text, reply_markup=markup)


# --- Command Handlers ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    is_new = not is_user_exist(user_id)
    register_user(user_id, username)
    
    if is_new:
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                referrer_id = int(args[1].replace("ref_", ""))
                if referrer_id != user_id:  
                    award_item(referrer_id, f"referral_{user_id}", REFERRAL_REWARD)
                    try:
                        bot.send_message(
                            referrer_id, 
                            f"🎉 *New Referral!*\n\n@{username} joined using your link. +${REFERRAL_REWARD:.2f} USDT added to your balance!",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
            except ValueError:
                pass
        
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    send_main_menu(message.chat.id, f"🎉 Welcome back, {username}! Your access is verified.")


@bot.callback_query_handler(func=lambda call: call.data == "verify_links")
def callback_verification(call):
    user_id = call.from_user.id
    if check_compulsory_join(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message.chat.id, "🎉 Access Unlocked! Welcome to the Extreme Earn Engine.")
    else:
        bot.answer_callback_query(call.id, "❌ Verification failed. Please ensure you have joined all platforms!", show_alert=True)


# --- Core Action Processing Navigation Loop ---
@bot.message_handler(func=lambda msg: True)
def menu_navigation(message):
    user_id = message.from_user.id
    
    # 🚨 LIVE GATE ENFORCEMENT: Checks membership status on EVERY single menu button push.
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    user_data = get_user_data(user_id)
    balance = user_data[0] if user_data else 0.0000
    wallet = user_data[1] if user_data else None

    if message.text == "📊 Balance":
        bot.send_message(message.chat.id, f"💰 *Your Current Balance:* ${balance:.2f} USDT", parse_mode="Markdown")

    elif message.text == "📋 Tasks":
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Generates all user-defined tasks dynamically with instant claim layouts
        for task_id, info in TASKS.items():
            if is_item_claimed(user_id, task_id):
                btn_text = f"✅ Claimed (- ${info['reward']:.2f})"
            else:
                btn_text = f"{info['text']} (+${info['reward']:.2f})"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"claim_{task_id}"))
        
        text = (
            "📋 *Available Microtasks & Offerwalls*\n\n"
            "Complete the app installations and streaming video items below to earn rewards directly:\n\n"
            "👉 *Tap on any open task below to start tracking verification:*"
        )
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

    elif message.text == "👥 Referrals":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        count = get_referral_count(user_id)
        total_earned = count * REFERRAL_REWARD
        
        text = (
            "👥 *Extreme Referral Dashboard*\n\n"
            "Invite network users to clear gates and earn automated payouts alongside your link asset structures!\n\n"
            f"💵 *Payout Rate:* ${REFERRAL_REWARD:.2f} USDT per active user\n"
            f"📊 *Your Metrics:* {count} successful invitations registered (${total_earned:.2f} USDT earned)\n\n"
            "🔗 *Your Unique Referral Link:*\n"
            f"`{ref_link}`\n\n"
            "Copy and share this link. Referrals must clear the compulsory community verification gate for rewards to drop!"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    elif message.text == "🎁 Bonus Code":
        msg = bot.send_message(
            message.chat.id, 
            "🎁 *Enter Promo Bonus Code*\n\nType your special configuration bonus code below to unlock system metrics:",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_bonus_code_claim)

    elif message.text == "💼 Wallet Setup":
        text = (
            f"💼 *Your Wallet Status:* `{wallet if wallet else 'Not Configured'}`\n\n"
            "⚠️ *Recommended Action:*\n"
            "We highly request payouts to secure decentralized accounts. "
            f"Please download [Trust Wallet here]({TRUST_WALLET_URL}) if you don't have one.\n\n"
            "👉 *To set or change your USDT wallet address, reply directly to this message with your address now.*"
        )
        msg = bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(msg, process_wallet_save)

    elif message.text == "💵 Withdraw Status":
        if not wallet:
            return bot.send_message(
                message.chat.id, 
                f"❌ You cannot withdraw! Please set your payout address first via *💼 Wallet Setup*. We highly recommend using [Trust Wallet]({TRUST_WALLET_URL}).", 
                parse_mode="Markdown"
            )
        
        if balance < 2.00:
            return bot.send_message(message.chat.id, f"❌ Minimum withdrawal threshold is *$2.00 USD*. Your current metric is: ${balance:.2f} USD.", parse_mode="Markdown")

        msg = bot.send_message(message.chat.id, f"💵 *Available to Cashout:* ${balance:.2f} USD\n\nReply with the exact numerical amount you want to withdraw:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_withdrawal_request, balance, wallet)


# --- Task Inline Callbacks Processing ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("claim_"))
def process_task_claims(call):
    user_id = call.from_user.id
    
    # Verify channel membership status when executing callback actions
    if not check_compulsory_join(user_id):
        bot.answer_callback_query(call.id, "❌ Verification Required! Please join our channels first.", show_alert=True)
        return send_verification_gate(call.message.chat.id)
        
    task_id = call.data.replace("claim_", "")
    
    if task_id not in TASKS:
        return bot.answer_callback_query(call.id, "❌ Unknown Task Configuration.", show_alert=True)
        
    if is_item_claimed(user_id, task_id):
        return bot.answer_callback_query(call.id, "❌ You have already completed this task and claimed your reward!", show_alert=True)
    
    reward = TASKS[task_id]["reward"]
    success = award_item(user_id, task_id, reward)
    if success:
        bot.answer_callback_query(call.id, f"🎉 Success! +${reward:.2f} USDT added to your balance.", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message.chat.id, "📊 Account balance successfully adjusted. Select an option to continue:")
    else:
        bot.answer_callback_query(call.id, "⚠️ Database processing error. Please try again later.", show_alert=True)


# --- Conversation Logic Flow ---
def process_bonus_code_claim(message):
    user_id = message.from_user.id
    
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    input_code = message.text.strip().lower()
    
    if input_code != "muiz":
        return bot.send_message(message.chat.id, "❌ Invalid Bonus Code. Please verify your credentials and try again.")
        
    if is_item_claimed(user_id, "bonus_muiz"):
        return bot.send_message(message.chat.id, "❌ System Error: You have already claimed this specific $2.00 bonus package!")
        
    success = award_item(user_id, "bonus_muiz", 2.0000)
    if success:
        bot.send_message(message.chat.id, "🎉 *Code Accepted!*\n\n$2.00 USD has been credited permanently to your balance dashboard profiles!", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ System connectivity failure. Payout update aborted.")

def process_wallet_save(message):
    user_id = message.from_user.id
    
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    wallet_address = message.text.strip()
    if len(wallet_address) < 25 or " " in wallet_address:
        return bot.send_message(message.chat.id, "❌ Invalid address layout. Please select '💼 Wallet Setup' and input a real crypto address network key.")
    
    update_wallet(user_id, wallet_address)
    bot.send_message(message.chat.id, f"✅ *Wallet Settings Saved Successfully!*\n\nYour future settlements will deploy to:\n`{wallet_address}`", parse_mode="Markdown")

def process_withdrawal_request(message, current_balance, wallet_address):
    user_id = message.from_user.id
    
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    try:
        amount = float(message.text.strip())
        if amount <= 0 or amount > current_balance:
            return bot.send_message(message.chat.id, "❌ Amount exceeds available assets or is invalid.")
        
        new_balance = float(current_balance) - amount
        update_balance(user_id, new_balance)

        # Alerts dispatched directly to your personal admin configuration panel
        admin_alert_text = (
            "⚡ NEW WITHDRAWAL REQUEST ⚡\n"
            "🗲\n"
            "───────────────────────\n\n"
            f"• User ID : {user_id}\n"
            f"• Amount  : ${amount:.2f} USD\n"
            f"• Wallet  : {wallet_address}\n"
            f"• Platform : Extreme\n\n"
            "───────────────────────\n\n"
            "Kindly verify my metrics and approve my payout."
        )

        bot.send_message(ADMIN_CHAT_ID, admin_alert_text)
        
        bot.send_message(
            message.chat.id, 
            f"🚀 *Request Received Successfully!*\n\n${amount:.2f} USD has been queued. Verification metrics have been dispatched to the settlement office. Please await admin clearing.",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ Error. Please enter numbers only (e.g., 2.10).")


if __name__ == "__main__":
    print("Bot engine fully connected and scanning logs...")
    bot.infinity_polling()
