import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import urllib.parse

# =====================================================================
# ⚙️ SYSTEM CONFIGURATION - ENTERPRISE METRICS
# =====================================================================
BOT_TOKEN = "8366284497:AAGqy2V6Mh5HI_GmNn15kh_bm0-x2BzplQw"              # Your Live BotToken
TG_CHANNEL = "@legitupdateontelegram"            # Enforced Verification Channel
WA_CHANNEL_LINK = "https://whatsapp.com/channel/0029VbDKfJQHFxPAOJsTfE3y" 

# Manual Payout Routing Target (Admin WhatsApp)
WHATSAPP_PAYOUT_NUMBER = "+2349034070745"

# Platform Reward Valuations (USD Tiers)
MIN_WITHDRAWAL = 2.0  
REFERRAL_REWARD = 0.2 
TASK_REWARD = 0.1     

# Wallet Ecosystem Settings
RECOMMENDED_WALLET = "Trust Wallet"
WALLET_DOWNLOAD_LINK = "https://trustwallet.com/download"
# =====================================================================

bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    """Initializes the secure SQL relational ledger structure locally on device."""
    db_path = os.path.join(os.getcwd(), "earning_platform.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0.0,
        referred_by INTEGER DEFAULT NULL,
        wallet_address TEXT DEFAULT NULL,
        verified_member INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

# Start the database engine immediately on run
init_db()

# --- BACKEND PIPELINE ENGINE UTILITIES ---

def check_tg_membership(user_id):
    """Queries Telegram server clusters to verify authentic channel membership status."""
    try:
        member = bot.get_chat_member(TG_CHANNEL, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

def render_dashboard_ui(user_id):
    """Compiles the dynamic front-facing user profile and menu navigation architecture."""
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
    user_profile = c.fetchone()
    conn.close()
    
    balance = user_profile[0] if user_profile else 0.0
    raw_wallet = user_profile[1] if user_profile else None
    
    if raw_wallet and len(str(raw_wallet)) > 15:
        wallet_display = f"{raw_wallet[:6]}...{raw_wallet[-6:]}"
    else:
        wallet_display = "None Registered"
        
    dashboard_text = (
        "💼 *PREMIUM EARNING HUB*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Account Balance  : `${balance:.2f} USD`\n"
        f"💳 Payout Wallet     : `{wallet_display}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Select an active operation matrix from the interface options below:"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Get Task", callback_data="ui_task"),
        InlineKeyboardButton("👥 Invite Friends", callback_data="ui_invite")
    )
    markup.add(
        InlineKeyboardButton("⚙️ Set/View Wallet", callback_data="ui_wallet"),
        InlineKeyboardButton("💳 Withdraw Funds", callback_data="ui_withdraw")
    )
    return dashboard_text, markup

# --- CORE USER TRAFFIC ROUTERS ---

@bot.message_handler(commands=['start'])
def handle_incoming_user(message):
    user_id = message.from_user.id
    cmd_args = message.text.split()
    
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user_exists = c.fetchone()
    
    if not user_exists:
        referrer_id = None
        if len(cmd_args) > 1 and cmd_args[1].isdigit():
            potential_id = int(cmd_args[1])
            if potential_id != user_id:
                referrer_id = potential_id
                
        c.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id))
        conn.commit()
    conn.close()

    # Subscription Gatekeeper Enforcement
    if not check_tg_membership(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📢 Join Official Telegram", url=f"https://t.me/{TG_CHANNEL.strip('@')}"),
            InlineKeyboardButton("🟢 Join Official WhatsApp", url=WA_CHANNEL_LINK),
            InlineKeyboardButton("🔄 Verify Membership Activation", callback_data="ui_verify_gate")
        )
        gate_msg = (
            "🔒 *ACCOUNT ACTIVATION REQUIRED*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "To maintain a clean platform ecosystem, you must enter our distribution updates channels before working.\n\n"
            "Please click both panels below to follow, then execute verification to unlock your account control board."
        )
        bot.send_message(user_id, gate_msg, reply_markup=markup, parse_mode="Markdown")
        return

    text, markup = render_dashboard_ui(user_id)
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def process_ui_interactions(call):
    user_id = call.from_user.id
    
    if call.data == "ui_verify_gate":
        if check_tg_membership(user_id):
            conn = sqlite3.connect("earning_platform.db")
            c = conn.cursor()
            c.execute("SELECT referred_by, verified_member FROM users WHERE user_id = ?", (user_id,))
            status = c.fetchone()
            
            if status and status[1] == 0:
                referrer, already_verified = status
                c.execute("UPDATE users SET verified_member = 1 WHERE user_id = ?", (user_id,))
                
                if referrer:
                    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REFERRAL_REWARD, referrer))
                    try:
                        alert_msg = (
                            "🚀 *REFERRAL MILESTONE SUCCESSFUL*\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"An onboarded invite link partner has completed verification checks! *+${REFERRAL_REWARD:.2f} USD* has been applied to your ledger account balance."
                        )
                        bot.send_message(referrer, alert_msg, parse_mode="Markdown")
                    except Exception:
                        pass
                conn.commit()
            conn.close()
            
            text, markup = render_dashboard_ui(user_id)
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Subscriptions Verification Dropped. Verify you are inside our Telegram channel structure.", show_alert=True)

    elif call.data == "ui_invite":
        bot_identity = bot.get_me()
        referral_link = f"https://t.me/{bot_identity.username}?start={user_id}"
        invite_msg = (
            "👥 *AFFILIATE ONBOARDING CORE*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Acquire network balance rewards by processing user joins via your specific link format tracking metrics.\n\n"
            f"💰 Invitation Reward: *${REFERRAL_REWARD:.2f} USD* upon gate clearance verification.\n\n"
            f"🔗 *Tracking Link Address:*\n`{referral_link}`"
        )
        bot.send_message(user_id, invite_msg, parse_mode="Markdown")

    elif call.data == "ui_task":
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (TASK_REWARD, user_id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"✅ Activity Task Cleared! +${TASK_REWARD:.2f} USD credited.", show_alert=True)
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "ui_wallet":
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("SELECT wallet_address FROM users WHERE user_id = ?", (user_id,))
        current_wallet = c.fetchone()[0]
        conn.close()
        
        wallet_display = current_wallet if current_wallet else "None Registered"
        prompt_text = (
            "⚙️ *SETTLEMENT WALLET MATRIX*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Current Routing Target: `{wallet_display}`\n\n"
            "⚡ *HIGH SPEED HIGH PROCESSING RECOMMENDATION:*\n"
            f"We strongly suggest using **{RECOMMENDED_WALLET}** to receive funds. Due to instant ledger visibility, Trust Wallet allocations complete processing significantly faster with absolute security control panels.\n\n"
            "⚠️ Notice: DO NOT apply exchange deposit strings (e.g., direct custodial addresses from Binance app), as batch transactions might get dropped or cause extreme clearing holds.\n\n"
            f"📥 [Download Trust Wallet App officially here]({WALLET_DOWNLOAD_LINK})\n\n"
            "👉 *To update:* Reply directly to this system message with your active *BEP-20 (BSC) USDT* wallet string address:"
        )
        prompt = bot.send_message(user_id, prompt_text, parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(prompt, save_wallet_routing)

    elif call.data == "ui_withdraw":
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
        balance, wallet = c.fetchone()
        conn.close()
        
        if not wallet:
            bot.answer_callback_query(call.id, "❌ Action Required: You must link a payout address via 'Set Wallet' menu first.", show_alert=True)
        elif balance < MIN_WITHDRAWAL:
            bot.answer_callback_query(call.id, f"❌ Payout Threshold Insufficient: Minimum target benchmark limit is ${MIN_WITHDRAWAL:.2f} USD.", show_alert=True)
        else:
            # 📝 Generate clean text parameters for the WhatsApp URL string
            raw_text = (
                f"⚡ NEW WITHDRAWAL REQUEST ⚡\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• User ID  : {user_id}\n"
                f"• Amount   : ${balance:.2f} USD\n"
                f"• Wallet   : {wallet}\n"
                f"• Platform : Extreme\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Kindly verify my metrics and approve my payout."
            )
            # Safely encode the message formatting to prevent breaking links
            encoded_text = urllib.parse.quote(raw_text)
            whatsapp_url = f"https://wa.me/{WHATSAPP_PAYOUT_NUMBER.replace('+', '')}?text={encoded_text}"
            
            confirm_ui = InlineKeyboardMarkup()
            confirm_ui.add(InlineKeyboardButton("🟢 Open WhatsApp to Claim Funds", url=whatsapp_url))
            
            withdraw_card = (
                "⚠️ *CONFIRM LIQUIDATION REQUEST*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Total Liquidation Value : `${balance:.2f} USD`\n"
                f"Target Network Router   : `USDT (BEP-20)`\n"
                f"Settlement Destination  : `{wallet}`\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ *NOTICE:* For the **fastest automated distribution execution**, ensure this configuration setup matches your custom **{RECOMMENDED_WALLET}**.\n\n"
                "Click the button below to transfer your details securely to our support team over WhatsApp for instant manual processing."
            )
            bot.send_message(user_id, withdraw_card, reply_markup=confirm_ui, parse_mode="Markdown")

def save_wallet_routing(message):
    user_id = message.from_user.id
    input_address = message.text.strip()
    
    # Standard EVM address checks
    if not input_address.startswith("0x") or len(input_address) < 40:
        bot.send_message(user_id, "❌ *INPUT ROUTING REJECTED*\n\nThe syntax structure provided is not an authentic crypto public address. Setup dropped.")
        return
        
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (input_address, user_id))
    conn.commit()
    conn.close()
    
    bot.send_message(user_id, f"✅ *ROUTING PIPELINE LINKED*\n\nYour profile settlement tracking destination has been updated to:\n`{input_address}`", parse_mode="Markdown")

if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 PREMIUM TELEGRAM NETWORK BOT ENGINE DEPLOYED")
    print("📡 Local daemon monitoring active traffic flows...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.infinity_polling()
