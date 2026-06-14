import os
import psycopg2
import telebot
from telebot import types

# Load variables from Render Environment configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
# Your personal account numerical ID (retrieved via @userinfobot)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Platform configuration details
TELEGRAM_CHANNEL_ID = -1002485960123  # 🔴 REPLACE WITH YOUR ACTUAL NEGATIVE 13-DIGIT CHANNEL ID
TG_LINK = "https://t.me/+UkdkPcVoAMU2YTM0"
WHATSAPP_LINK = "https://chat.whatsapp.com/EZgSS4NS4vKB6Uqtx1NiTH"
TRUST_WALLET_URL = "https://trustwallet.com/download"

bot = telebot.TeleBot(BOT_TOKEN)

# --- Database Helper Functions ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

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
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET wallet_address = %s WHERE telegram_id = %s;", (wallet, user_id))
            conn.commit()

def update_balance(user_id, new_balance):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET balance = %s WHERE telegram_id = %s;", (new_balance, user_id))
            conn.commit()


# --- Verification Gate Check ---
def check_compulsory_join(user_id):
    """Returns True if user is in the Telegram channel, False otherwise."""
    try:
        member = bot.get_chat_member(TELEGRAM_CHANNEL_ID, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception:
        # If bot isn't admin yet or ID configuration is missing, default pass to protect uptime
        return True

def send_verification_gate(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 Join Telegram Channel", url=TG_LINK),
        types.InlineKeyboardButton("💬 Join WhatsApp Group", url=WHATSAPP_LINK),
        types.InlineKeyboardButton("🔄 Verify Membership", callback_data="verify_links")
    )
    
    text = (
        "⚠️ **Access Denied - Verification Required!**\n\n"
        "To protect our network, you must join our compulsory channels "
        "before you can use any bot commands or earn rewards.\n\n"
        "Join both platforms below and hit Verify!"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


# --- Main Menu Generator ---
def send_main_menu(chat_id, text="Main Dashboard Loaded! Choose an option below to start earning:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📋 Tasks"),
        types.KeyboardButton("💼 Wallet Setup"),
        types.KeyboardButton("💵 Withdraw Status"),
        types.KeyboardButton("📊 Balance")
    )
    bot.send_message(chat_id, text, reply_markup=markup)


# --- Bot Handlers ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    register_user(user_id, username)
    
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    send_main_menu(message.chat.id, f"🎉 Welcome back, {username}! Access granted. Ready to accumulate metrics?")


@bot.callback_query_handler(func=lambda call: call.data == "verify_links")
def callback_verification(call):
    user_id = call.from_user.id
    if check_compulsory_join(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message.chat.id, "🎉 Access Unlocked! Welcome to the Extreme Earn Engine.")
    else:
        bot.answer_callback_query(call.id, "❌ You have not joined both required groups yet!", show_alert=True)


# --- Menu Button Logic ---
@bot.message_handler(func=lambda msg: True)
def menu_navigation(message):
    user_id = message.from_user.id
    
    # Run the roadblock gate check first
    if not check_compulsory_join(user_id):
        return send_verification_gate(message.chat.id)
        
    user_data = get_user_data(user_id)
    balance = user_data[0] if user_data else 0.0000
    wallet = user_data[1] if user_data else None

    if message.text == "📊 Balance":
        bot.send_message(message.chat.id, f"💰 **Your Current Balance:** ${balance:.2f} USDT")

    elif message.text == "📋 Tasks":
        # Example Task Structure
        bot.send_message(message.chat.id, "⚙️ Tasks module loading... New monetization actions will appear here shortly.")

    elif message.text == "💼 Wallet Setup":
        text = (
            f"💼 **Your Wallet Status:** `{wallet if wallet else 'Not Configured'}`\n\n"
            "⚠️ **Recommended Action:**\n"
            "We highly request payouts to secure decentralized accounts. "
            f"Please download [Trust Wallet here]({TRUST_WALLET_URL}) if you don't have one.\n\n"
            "👉 **To set or change your USDT wallet address, reply directly to this message with your address now.**"
        )
        msg = bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(msg, process_wallet_save)

    elif message.text == "💵 Withdraw Status":
        if not wallet:
            return bot.send_message(message.chat.id, f"❌ You cannot withdraw! Please set your payout address first via **💼 Wallet Setup**. We highly recommend using [Trust Wallet]({TRUST_WALLET_URL}).", parse_mode="Markdown")
        
        if balance < 2.00:
            return bot.send_message(message.chat.id, f"❌ Minimum withdrawal threshold is **$2.00 USD**. Your current metric is: ${balance:.2f} USD.")

        msg = bot.send_message(message.chat.id, f"💵 **Available to Cashout:** ${balance:.2f} USD\n\nReply with the exact numerical amount you want to withdraw:")
        bot.register_next_step_handler(msg, process_withdrawal_request, balance, wallet)


# --- Context Action Collection Logic ---
def process_wallet_save(message):
    wallet_address = message.text.strip()
    if len(wallet_address) < 25:
        return bot.send_message(message.chat.id, "❌ Invalid address layout. Please select '💼 Wallet Setup' and input a real crypto address network key.")
    
    update_wallet(message.from_user.id, wallet_address)
    bot.send_message(message.chat.id, f"✅ Success! Your settlement address has been updated to:\n`{wallet_address}`", parse_mode="Markdown")

def process_withdrawal_request(message, current_balance, wallet_address):
    try:
        amount = float(message.text.strip())
        if amount <= 0 or amount > current_balance:
            return bot.send_message(message.chat.id, "❌ Amount exceeds available assets or is invalid.")
        
        user_id = message.from_user.id
        new_balance = float(current_balance) - amount
        update_balance(user_id, new_balance)

        # ⚡ Format matching your WhatsApp configuration layout ⚡
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

        # Dispatch straight to your personal account via ID
        bot.send_message(ADMIN_CHAT_ID, admin_alert_text)
        
        bot.send_message(
            message.chat.id, 
            f"🚀 **Request Received Successfully!**\n\n${amount:.2f} USD has been queued. Verification metrics have been dispatched to the settlement office. Please await admin clearing."
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ Error. Please enter numbers only (e.g., 2.10).")


# Start polling loop
if __name__ == "__main__":
    print("Bot is tracking and live...")
    bot.infinity_polling()
