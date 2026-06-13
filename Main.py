import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import random
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# =====================================================================
# ⚙️ SYSTEM CONFIGURATION - ENTERPRISE METRICS
# =====================================================================
BOT_TOKEN = "8366284497:AAGqy2V6Mh5HI_GmNn15kh_bm0-x2BzplQw"              # Your Live BotToken
TG_CHANNEL = "@legitupdateontelegram"            # Enforced Verification Channel
WA_CHANNEL_LINK = "https://whatsapp.com/channel/0029VbDKfJQHFxPAOJsTfE3y" 
YT_CHANNEL_LINK = "https://www.youtube.com/@beaconofslam"

# Secure Target Group Link ID for Internal Payout Ledger Clearing
ADMIN_GROUP_CHAT_ID = -1002345869042  # Internal Routing Group Mapping

# Platform Reward Valuations (USD Tiers)
MIN_WITHDRAWAL = 2.0  
REFERRAL_REWARD = 0.2 
TASK_REWARD = 0.10     # Auto-credited instantly after 15 seconds video watch check

# Wallet Ecosystem Settings
RECOMMENDED_WALLET = "Trust Wallet"
WALLET_DOWNLOAD_LINK = "https://trustwallet.com/download"

# 🎬 AUTOMATED AD ROTATION ENGINE (4 YouTube Shorts Assets)
VIDEO_TASKS = [
    "https://youtube.com/shorts/3uDPXXJbfr8?si=z6fWdUhxeMRuthuw",
    "https://youtube.com/shorts/tWLKPUv5vUw?si=0kMIO-fRL69X1m2X",
    "https://youtube.com/shorts/JfinwV1CFuc?si=j52Y6BsYACCMwUmS",
    "https://youtube.com/shorts/sT93F-rFmob"
]
# =====================================================================

bot = telebot.TeleBot(BOT_TOKEN)

# Hidden runtime dictionary to keep track of user watch time and clicks
user_watch_tracker = {}

def init_db():
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

init_db()

# --- CLOUD ALIVE KEEPER (HTTP SERVER FOR RENDER HEALTH CHECKS) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"EXTREME ENGINE RUNNING LIVE")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- BACKEND PIPELINE ENGINE UTILITIES ---

def check_tg_membership(user_id):
    try:
        member = bot.get_chat_member(TG_CHANNEL, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

def render_dashboard_ui(user_id):
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

    if not check_tg_membership(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📢 1. Join Official Telegram", url=f"https://t.me/{TG_CHANNEL.strip('@')}"),
            InlineKeyboardButton("🔴 2. Subscribe To Our YouTube", url=YT_CHANNEL_LINK),
            InlineKeyboardButton("🟢 3. Join Official WhatsApp", url=WA_CHANNEL_LINK),
            InlineKeyboardButton("🔄 Verify Membership Activation", callback_data="ui_verify_gate")
        )
        gate_msg = (
            "🔒 *ACCOUNT ACTIVATION REQUIRED*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "To maintain a clean platform ecosystem, you must complete our distribution channel onboarding tasks before working.\n\n"
            "Please click all 3 panels above to join and subscribe, then execute verification to unlock your account control board."
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
            
            try: bot.answer_callback_query(call.id, "✅ Verification Passed!")
            except Exception: pass
                
            text, markup = render_dashboard_ui(user_id)
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
        else:
            try: bot.answer_callback_query(call.id, "❌ Join the channels first!", show_alert=True)
            except Exception: pass
            
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("📢 1. Join Official Telegram", url=f"https://t.me/{TG_CHANNEL.strip('@')}"),
                InlineKeyboardButton("🔴 2. Subscribe To Our YouTube", url=YT_CHANNEL_LINK),
                InlineKeyboardButton("🟢 3. Join Official WhatsApp", url=WA_CHANNEL_LINK),
                InlineKeyboardButton("🔄 Verify Membership Activation", callback_data="ui_verify_gate")
            )
            bot.send_message(user_id, "⚠️ *Access Denied:* Please ensure you have joined our Telegram channel, subscribed to our YouTube, and entered our WhatsApp stream before hitting verification.", reply_markup=markup, parse_mode="Markdown")

    elif call.data == "ui_invite":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        bot_identity = bot.get_me()
        referral_link = f"https://t.me/{bot_identity.username}?start={user_id}"
        invite_msg = (
            "👥 *AFFILIATE ONBOARDING CORE*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Invitation Reward: *${REFERRAL_REWARD:.2f} USD*\n\n"
            f"🔗 *Tracking Link Address:*\n`{referral_link}`"
        )
        bot.send_message(user_id, invite_msg, parse_mode="Markdown")

    elif call.data == "ui_task":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        step1_markup = InlineKeyboardMarkup()
        step1_markup.add(InlineKeyboardButton("➡️ Proceed to Video Task", callback_data="execute_video_launch"))
        
        bot.send_message(
            user_id, 
            "📋 *NEW REWARD TASK FOUND!*\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Reward Value: *${TASK_REWARD:.2f} USD*\n"
            "Task Type: YouTube Watch & Subscribe\n\n"
            "Tap the button below to initialize your task stream secure connection.", 
            reply_markup=step1_markup, 
            parse_mode="Markdown"
        )

    elif call.data == "execute_video_launch":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        selected_video_url = random.choice(VIDEO_TASKS)
        user_watch_tracker[user_id] = {"start_time": time.time(), "clicked": True}
        
        task_markup = InlineKeyboardMarkup(row_width=1)
        task_markup.add(
            InlineKeyboardButton("📺 Open Video Link & Subscribe Now", url=selected_video_url),
            InlineKeyboardButton("🔄 Verify Video Task Completed", callback_data="ui_verify_watch_time")
        )
        
        task_msg = (
            "🎬 *TASK PROCESSING STARTED*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Click the **Open Video Link** button below immediately.\n"
            "2. Watch the video fully for **at least 15 seconds**.\n"
            "3. Make sure to **Subscribe** to the channel.\n"
            "4. Return here and click **Verify Video Task Completed** to claim your earnings."
        )
        bot.send_message(user_id, task_msg, reply_markup=task_markup, parse_mode="Markdown")

    elif call.data == "ui_verify_watch_time":
        if user_id not in user_watch_tracker:
            try: bot.answer_callback_query(call.id, "❌ Click 'Proceed to Video Task' first!", show_alert=True)
            except Exception: pass
            return
            
        elapsed_time = time.time() - user_watch_tracker[user_id]["start_time"]
        
        if elapsed_time < 15.0:
            remaining = int(15 - elapsed_time)
            try: 
                bot.answer_callback_query(call.id, f"⚠️ Access Denied: You must watch the video for 15 seconds! ({remaining}s remaining)", show_alert=True)
            except Exception: 
                pass
            return
            
        user_watch_tracker.pop(user_id, None)
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (TASK_REWARD, user_id))
        conn.commit()
        conn.close()
        
        try: bot.answer_callback_query(call.id, f"🎉 Success! +${TASK_REWARD:.2f} USD added.", show_alert=True)
        except Exception: pass
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, f"✅ *TASK CREDITED SUCCESSFULLY*\n━━━━━━━━━━━━━━━━━━━━━━━━\nYour watch metrics verified perfectly! *+${TASK_REWARD:.2f} USD* has been added to your balance. Make sure you stay subscribed!", parse_mode="Markdown")
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "ui_wallet":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
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
            "⚡ *HIGH SPEED RUNNING PROCESS RECOMMENDATION:*\n"
            f"We strongly suggest using **{RECOMMENDED_WALLET}** to receive funds instantly.\n\n"
            f"📥 [Download Trust Wallet App officially here]({WALLET_DOWNLOAD_LINK})\n\n"
            "👉 *To update:* Reply directly with your active *BEP-20 (BSC) USDT* address:"
        )
        prompt = bot.send_message(user_id, prompt_text, parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(prompt, save_wallet_routing)

    elif call.data == "ui_withdraw":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
        balance, wallet = c.fetchone()
        
        if not wallet:
            conn.close()
            bot.send_message(user_id, "❌ *Action Required:* Link a wallet address first.", parse_mode="Markdown")
            return
            
        if balance < MIN_WITHDRAWAL:
            conn.close()
            bot.send_message(user_id, f"❌ Minimum withdrawal target limit is `${MIN_WITHDRAWAL:.2f} USD`.", parse_mode="Markdown")
            return
            
        c.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        admin_invoice_msg = (
            "⚡ *NEW TRANSACTION REQUEST SUBMITTED*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User ID     : `{user_id}`\n"
            f"💰 Value Tiers : `${balance:.2f} USD`\n"
            f"💳 Destination : `{wallet}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚙️ Status: *Ledger balance zeroed out. Ready for manual payment distribution.*"
        )
        
        try:
            bot.send_message(ADMIN_GROUP_CHAT_ID, admin_invoice_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"⚠️ Network error forwarding transaction: {e}")
            
        client_receipt_card = (
            "✅ *WITHDRAWAL INVOICE SUBMITTED FOR REVIEW*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Liquidation Value Recieved : `${balance:.2f} USD`\n"
            f"Target Destination Wallet  : `{wallet}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏳ *PROCESSING TIMELINE WINDOW:*\n"
            f"• If you utilized **{RECOMMENDED_WALLET}**, your settlement balance will be credited within **1 Hour**!\n\n"
            "• If you utilized any external exchange wallet address, accounting checks
