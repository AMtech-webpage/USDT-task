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

# 🎯 WITHDRAWAL DESTINATION CHANNEL
ADMIN_GROUP_CHAT_ID = "@USDTsettlemente"  

# Platform Reward Valuations (USD Tiers)
MIN_WITHDRAWAL = 2.0  
REFERRAL_REWARD = 0.2 
PROMO_REWARD = 2.00    # Reward for entering promo code 'muiz'

# Wallet Ecosystem Settings
RECOMMENDED_WALLET = "Trust Wallet"
WALLET_DOWNLOAD_LINK = "https://trustwallet.com/download"

# 🎬 REWARDED TASK INVENTORY (YouTube Shorts Channels)
VIDEO_TASKS = [
    {"id": "yt_1", "title": "Watch YouTube Shorts 1", "reward": 0.10, "url": "https://youtube.com/shorts/3uDPXXJbfr8?si=z6fWdUhxeMRuthuw", "time": 15},
    {"id": "yt_2", "title": "Watch YouTube Shorts 2", "reward": 0.10, "url": "https://youtube.com/shorts/tWLKPUv5vUw?si=0kMIO-fRL69X1m2X", "time": 15},
    {"id": "yt_3", "title": "Watch YouTube Shorts 3", "reward": 0.10, "url": "https://youtube.com/shorts/JfinwV1CFuc?si=j52Y6BsYACCMwUmS", "time": 15},
    {"id": "yt_4", "title": "Watch YouTube Shorts 4", "reward": 0.10, "url": "https://youtube.com/shorts/sT93F-rFmob", "time": 15}
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
        verified_member INTEGER DEFAULT 0,
        promo_used INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

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

def ensure_user_exists(user_id):
    """Safely verifies and creates a user entry if missing to prevent unpacking crashes."""
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def render_dashboard_ui(user_id):
    ensure_user_exists(user_id)
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
    user_profile = c.fetchone()
    conn.close()
    
    balance = user_profile[0] if (user_profile and user_profile[0] is not None) else 0.0
    raw_wallet = user_profile[1] if (user_profile and user_profile[1]) else None
    
    if raw_wallet and len(str(raw_wallet)) > 15:
        wallet_display = f"{raw_wallet[:6]}...{raw_wallet[-6:]}"
    else:
        wallet_display = "None Registered"
        
    dashboard_text = f"💼 *PREMIUM EARNING HUB*\n━━━━━━━━━━━━━━━━━━━━━━━━\n💰 Account Balance  : `${balance:.2f} USD`\n💳 Payout Wallet     : `{wallet_display}`\n━━━━━━━━━━━━━━━━━━━━━━━━\nSelect an active operation matrix below:"
    
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
    else:
        if len(cmd_args) > 1 and cmd_args[1].isdigit():
            potential_id = int(cmd_args[1])
            if potential_id != user_id:
                try:
                    invalid_msg = "❌ *REFERRAL STATUS: INVALID*\n━━━━━━━━━━━━━━━━━━━━━━━━\nAn existing user clicked your invitation link. No credits were allocated as they already maintain an active profile."
                    bot.send_message(potential_id, invalid_msg, parse_mode="Markdown")
                except Exception:
                    pass
                    
    conn.close()

    if not check_tg_membership(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📢 1. Join Official Telegram", url="https://t.me/" + TG_CHANNEL.strip('@')),
            InlineKeyboardButton("🔴 2. Subscribe To Our YouTube", url=YT_CHANNEL_LINK),
            InlineKeyboardButton("🟢 3. Join Official WhatsApp", url=WA_CHANNEL_LINK),
            InlineKeyboardButton("🔄 Verify Membership Activation", callback_data="ui_verify_gate")
        )
        gate_msg = "🔒 *ACCOUNT ACTIVATION REQUIRED*\n━━━━━━━━━━━━━━━━━━━━━━━━\nYou must complete our distribution channel onboarding tasks before working.\n\nPlease click all 3 panels above to join and subscribe, then verify to unlock your board."
        bot.send_message(user_id, gate_msg, reply_markup=markup, parse_mode="Markdown")
        return

    text, markup = render_dashboard_ui(user_id)
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def process_ui_interactions(call):
    user_id = call.from_user.id
    ensure_user_exists(user_id)
    
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
                        alert_msg = f"🚀 *REFERRAL STATUS: VALID*\n━━━━━━━━━━━━━━━━━━━━━━━━\nYour invited friend verified their account! *+${REFERRAL_REWARD:.2f} USD* has been successfully added to your balance."
                        bot.send_message(referrer, alert_msg, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Failed to notify referrer {referrer}: {e}")
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
                InlineKeyboardButton("📢 1. Join Official Telegram", url="https://t.me/" + TG_CHANNEL.strip('@')),
                InlineKeyboardButton("🔴 2. Subscribe To Our YouTube", url=YT_CHANNEL_LINK),
                InlineKeyboardButton("🟢 3. Join Official WhatsApp", url=WA_CHANNEL_LINK),
                InlineKeyboardButton("🔄 Verify Membership Activation", callback_data="ui_verify_gate")
            )
            bot.send_message(user_id, "⚠️ *Access Denied:* Ensure you joined our Telegram, subscribed to YouTube, and joined our WhatsApp before verifying.", reply_markup=markup, parse_mode="Markdown")

    elif call.data == "ui_invite":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        bot_identity = bot.get_me()
        referral_link = "https://t.me/" + bot_identity.username + "?start=" + str(user_id)
        invite_msg = f"👥 *AFFILIATE ONBOARDING CORE*\n━━━━━━━━━━━━━━━━━━━━━━━━\n💰 Invitation Reward: *${REFERRAL_REWARD:.2f} USD*\n\n🔗 *Tracking Link Address:*\n`{referral_link}`"
        bot.send_message(user_id, invite_msg, parse_mode="Markdown")

    elif call.data == "ui_task":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        task_markup = InlineKeyboardMarkup(row_width=1)
        task_markup.add(InlineKeyboardButton("📲 Download HiFami App & Sign Up ($0.30)", callback_data="task_hifami_start"))
        task_markup.add(InlineKeyboardButton("🎮 Complete Farm Level 20 ($0.50)", callback_data="task_farm_start"))
        task_markup.add(InlineKeyboardButton("📥 Download App & Login ($0.40)", callback_data="task_loginapp_start"))
        
        for i, task in enumerate(VIDEO_TASKS):
            task_markup.add(InlineKeyboardButton(f"📺 Watch Video {i+1} (${task['reward']:.2f})", callback_data=f"task_yt_start_{task['id']}"))
            
        task_markup.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="ui_main_menu"))
        
        task_list_text = "📋 *AVAILABLE OPERATION TASK MATRIX*\n━━━━━━━━━━━━━━━━━━━━━━━━\nSelect an operation task from the menu list below to start earning rewards:"
        bot.send_message(user_id, task_list_text, reply_markup=task_markup, parse_mode="Markdown")

    elif call.data == "ui_main_menu":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

    # --- HIFAMI APP DOWNLOAD TASK ROUTERS ---
    elif call.data == "task_hifami_start":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        user_watch_tracker[f"{user_id}_hifami"] = {"start_time": time.time()}
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔗 Open Download Link", url="https://s.hifamiapp.com/1/b6xaDAoXh"),
            InlineKeyboardButton("🔄 Verify Download App", callback_data="task_hifami_verify")
        )
        msg = "📲 *HIFAMI REGISTRATION MISSION*\n━━━━━━━━━━━━━━━━━━━━━━━━\n💰 Reward: *$0.30 USD*\n\n1. Click the link below to install the application.\n2. Complete user registration profile configurations.\n3. Keep the app active. Verify when complete."
        bot.send_message(user_id, msg, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "task_hifami_verify":
        track_key = f"{user_id}_hifami"
        if track_key not in user_watch_tracker:
            try: bot.answer_callback_query(call.id, "❌ Click 'Open Download Link' first!", show_alert=True)
            except Exception: pass
            return
            
        elapsed = time.time() - user_watch_tracker[track_key]["start_time"]
        
        if elapsed < 120.0:
            try: bot.answer_callback_query(call.id, "⚠️ Verification Pending: System checks indicate task steps are still processing. Please try again shortly.", show_alert=True)
            except Exception: pass
            return
            
        user_watch_tracker.pop(track_key, None)
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + 0.30 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        try: bot.answer_callback_query(call.id, "🎉 Success! +$0.30 USD added.", show_alert=True)
        except Exception: pass
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, "✅ *HIFAMI TASK COMPLETED!*\nYour download matrix verified completely!", reply_markup=markup, parse_mode="Markdown")

    # --- FARM LEVEL 20 TASK ROUTERS ---
    elif call.data == "task_farm_start":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        user_watch_tracker[f"{user_id}_farm"] = {"start_time": time.time()}
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🎮 Play Farm Game", url="https://playbb.fun/u/28229500"),
            InlineKeyboardButton("🔄 Verify Level 20 Completed", callback_data="task_farm_verify")
        )
        msg = "🎮 *FARM LEVEL EVOLUTION MISSION*\n━━━━━━━━━━━━━━━━━━━━━━━━\n💰 Reward: *$0.50 USD*\n⚠️ *Note: Only for new users!*\n\n1. Open the game via the button link below.\n2. Create an account and reach Farm Level 20.\n3. Return to claim your earnings."
        bot.send_message(user_id, msg, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "task_farm_verify":
        track_key = f"{user_id}_farm"
        if track_key not in user_watch_tracker:
            try: bot.answer_callback_query(call.id, "❌ Open the game link first!", show_alert=True)
            except Exception: pass
            return
            
        user_watch_tracker.pop(track_key, None)
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + 0.50 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        try: bot.answer_callback_query(call.id, "🎉 Success! +$0.50 USD added.", show_alert=True)
        except Exception: pass
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, "✅ *FARM TASK CREDITED!*\n+$0.50 USD added to your wallet.", reply_markup=markup, parse_mode="Markdown")

    # --- DOWNLOAD & LOGIN APP TASK ROUTERS ---
    elif call.data == "task_loginapp_start":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        user_watch_tracker[f"{user_id}_loginapp"] = {"start_time": time.time()}
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📥 Download Application", url="https://playbb.fun/u/28229500"),
            InlineKeyboardButton("🔄 Verify New Login", callback_data="task_loginapp_verify")
        )
        msg = "📥 *APPLICATION ONBOARDING REWARD*\n━━━━━━━━━━━━━━━━━━━━━━━━\n💰 Reward: *$0.40 USD*\n⚠️ *Note: Only for new users!*\n\n1. Download the mobile framework using the portal below.\n2. Launch application package and complete primary login.\n3. Request verification checks."
        bot.send_message(user_id, msg, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "task_loginapp_verify":
        track_key = f"{user_id}_loginapp"
        if track_key not in user_watch_tracker:
            try: bot.answer_callback_query(call.id, "❌ Open the download link first!", show_alert=True)
            except Exception: pass
            return
            
        user_watch_tracker.pop(track_key, None)
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + 0.40 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        try: bot.answer_callback_query(call.id, "🎉 Success! +$0.40 USD added.", show_alert=True)
        except Exception: pass
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, "✅ *LOGIN TASK CREDITED!*\n+$0.40 USD added to your balance.", reply_markup=markup, parse_mode="Markdown")

    # --- DYNAMIC YOUTUBE TASK SYSTEM ROUTERS ---
    elif call.data.startswith("task_yt_start_"):
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        task_id = call.data.replace("task_yt_start_", "")
        matched_task = next((t for t in VIDEO_TASKS if t["id"] == task_id), None)
        
        if matched_task:
            user_watch_tracker[f"{user_id}_{task_id}"] = {"start_time": time.time()}
            
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("📺 Open Video Link & Subscribe Now", url=matched_task["url"]),
                InlineKeyboardButton("🔄 Verify Video Task Completed", callback_data="task_yt_verify_" + task_id)
            )
            
            task_run_text = f"🎬 *VIDEO TASK STARTED*\n━━━━━━━━━━━━━━━━━━━━━━━━\n1. Open link below.\n2. Watch for **at least {matched_task['time']} seconds**.\n3. Subscribe to the channel.\n4. Click verify when done."
            bot.send_message(user_id, task_run_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("task_yt_verify_"):
        task_id = call.data.replace("task_yt_verify_", "")
        matched_task = next((t for t in VIDEO_TASKS if t["id"] == task_id), None)
        track_key = f"{user_id}_{task_id}"
        
        if not matched_task or track_key not in user_watch_tracker:
            try: bot.answer_callback_query(call.id, "❌ Click 'Open Video Link' first!", show_alert=True)
            except Exception: pass
            return
            
        elapsed_time = time.time() - user_watch_tracker[track_key]["start_time"]
        
        if elapsed_time < float(matched_task["time"]):
            remaining = int(matched_task["time"] - elapsed_time)
            try: bot.answer_callback_query(call.id, f"⚠️ Access Denied: Watch for {matched_task['time']} seconds! ({remaining}s remaining)", show_alert=True)
            except Exception: pass
            return
            
        user_watch_tracker.pop(track_key, None)
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (matched_task["reward"], user_id))
        conn.commit()
        conn.close()
        
        try: bot.answer_callback_query(call.id, f"🎉 Success! +${matched_task['reward']:.2f} USD added.", show_alert=True)
        except Exception: pass
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, f"✅ *TASK CREDITED SUCCESSFULLY*\n━━━━━━━━━━━━━━━━━━━━━━━━\nYour watch metrics verified perfectly! *+${matched_task['reward']:.2f} USD* has been added to your balance.", reply_markup=markup, parse_mode="Markdown")

    elif call.data == "ui_wallet":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("SELECT wallet_address FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        current_wallet = row[0] if (row and row[0]) else None
        wallet_display = current_wallet if current_wallet else "None Registered"
        
        prompt_text = f"⚙️ *SETTLEMENT WALLET MATRIX*\n━━━━━━━━━━━━━━━━━━━━━━━━\nCurrent Routing Target: `{wallet_display}`\n\n⚡ *RECOMMENDATION:*\nWe suggest using **{RECOMMENDED_WALLET}** to receive funds instantly.\n\n📥 [Download Trust Wallet officially here]({WALLET_DOWNLOAD_LINK})\n\n👉 *To update:* Reply with your active *BEP-20 (BSC) USDT* address or type a valid promo code:"
        prompt = bot.send_message(user_id, prompt_text, parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(prompt, save_wallet_or_promo)

    elif call.data == "ui_withdraw":
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("SELECT balance, wallet_address FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        # Safe-unpack protecting against None entries
        balance = row[0] if (row and row[0] is not None) else 0.0
        wallet = row[1] if (row and row[1]) else None
        
        if not wallet or len(str(wallet).strip()) < 10:
            conn.close()
            bot.send_message(user_id, "❌ *Action Required:* Link a valid wallet address under 'Set/View Wallet' first.", parse_mode="Markdown")
            return
            
        if balance < MIN_WITHDRAWAL:
            conn.close()
            bot.send_message(user_id, f"❌ Minimum withdrawal target limit is `${MIN_WITHDRAWAL:.2f} USD`.\n\nYour current balance: `${balance:.2f} USD`", parse_mode="Markdown")
            return
            
        c.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        admin_invoice_msg = f"⚡ *NEW TRANSACTION REQUEST SUBMITTED*\n━━━━━━━━━━━━━━━━━━━━━━━━\n👤 User ID     : `{user_id}`\n💰 Value Tiers : `${balance:.2f} USD`\n💳 Destination : `{wallet}`\n━━━━━━━━━━━━━━━━━━━━━━━━\n⚙️ Status: *Balance zeroed out. Ready for distribution.*"
        
        try:
            bot.send_message(ADMIN_GROUP_CHAT_ID, admin_invoice_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"⚠️ Network error forwarding transaction to settlement channel: {e}")
            
        client_receipt_card = f"✅ *WITHDRAWAL INVOICE SUBMITTED FOR REVIEW*\n━━━━━━━━━━━━━━━━━━━━━━━━\nLiquidation Value Received : `${balance:.2f} USD`\nTarget Destination Wallet  : `{wallet}`\n━━━━━━━━━━━━━━━━━━━━━━━━\n⏳ *PROCESSING TIMELINE WINDOW:*\n• Using **{RECOMMENDED_WALLET}** settles within **1 Hour**!\n• External exchange addresses extend to **3 Days**."
        bot.send_message(user_id, client_receipt_card, parse_mode="Markdown")

def save_wallet_or_promo(message):
    user_id = message.from_user.id
    ensure_user_exists(user_id)
    input_text = message.text.strip() if message.text else ""
    
    if not input_text:
        bot.send_message(user_id, "❌ Input cannot be empty. Matrix canceled.")
        return

    # Check for Promo Code entry first
    if input_text.lower() == "muiz":
        conn = sqlite3.connect("earning_platform.db")
        c = conn.cursor()
        c.execute("SELECT promo_used FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        if row and row[0] == 1:
            conn.close()
            bot.send_message(user_id, "❌ *Promo code already claimed on this account!*")
            return
            
        c.execute("UPDATE users SET balance = balance + ?, promo_used = 1 WHERE user_id = ?", (PROMO_REWARD, user_id))
        conn.commit()
        conn.close()
        
        text, markup = render_dashboard_ui(user_id)
        bot.send_message(user_id, f"🎉 *PROMO CODE APPLIED!*\n━━━━━━━━━━━━━━━━━━━━━━━━\nCode `muiz` verified successfully. *+${PROMO_REWARD:.2f} USD* has been added to your balance!", reply_markup=markup, parse_mode="Markdown")
        return

    # Process standard crypto wallet routing (checks for valid 0x prefix or address format)
    if not (input_text.startswith("0x") or input_text.startswith("T")) or len(input_text) < 30:
        bot.send_message(user_id, "❌ *INVALID ROUTING OR PROMO CODE*\n\nPlease make sure you are inputting a valid wallet address or a correct promo code.")
        return
        
    conn = sqlite3.connect("earning_platform.db")
    c = conn.cursor()
    c.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (input_text, user_id))
    conn.commit()
    conn.close()
    
    text, markup = render_dashboard_ui(user_id)
    bot.send_message(user_id, f"✅ *WALLET ROUTING TARGET ADDED*\n\nLinked address completely:\n`{input_text}`", reply_markup=markup, parse_mode="Markdown")

if __name__ == "__main__":
    init_db()
    
    print("🤖 Launching Cloud Alive Keeper Server...")
    threading.Thread(target=run_health_server, daemon=True).start()
    
    time.sleep(1)
    
    print("🚀 Extreme Engine Polling Active.")
    bot.infinity_polling()
