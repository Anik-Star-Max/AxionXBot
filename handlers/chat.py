from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from database import users, save_users
import time
import os
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")

RATE_LIMIT = {}  # {user_id: last_message_timestamp}
RATE_SECONDS = 1.5

def is_rate_limited(user_id):
    now = time.time()
    if user_id not in RATE_LIMIT or now - RATE_LIMIT[user_id] > RATE_SECONDS:
        RATE_LIMIT[user_id] = now
        return False
    return True

# Typing action decorator
def send_typing_action(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        return await func(update, context)
    return wrapper

@send_typing_action
async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chatting_with")

    if is_rate_limited(user_id):
        await update.message.reply_text("⏱ Slow down a bit!")
        return

    if partner_id and partner_id in users:
        if update.message.text:
            await context.bot.send_message(chat_id=int(partner_id), text=update.message.text)
        elif update.message.photo:
            await context.bot.send_photo(chat_id=int(partner_id), photo=update.message.photo[-1].file_id)
        elif update.message.sticker:
            await context.bot.send_sticker(chat_id=int(partner_id), sticker=update.message.sticker.file_id)
        elif update.message.document:
            await context.bot.send_document(chat_id=int(partner_id), document=update.message.document.file_id)
        elif update.message.voice:
            await context.bot.send_voice(chat_id=int(partner_id), voice=update.message.voice.file_id)
        elif update.message.video:
            await context.bot.send_video(chat_id=int(partner_id), video=update.message.video.file_id)
        else:
            await update.message.reply_text("⚠️ Unsupported message type.")
    else:
        await update.message.reply_text("❌ You're not chatting with anyone. Use /next to connect.")

# ===============================
# 🔴 Stop Chat
@send_typing_action
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chatting_with")

    if partner_id and partner_id in users:
        users[user_id]["chatting_with"] = None
        users[partner_id]["chatting_with"] = None
        save_users()

        await update.message.reply_text("❌ Chat ended.")
        try:
            await context.bot.send_message(chat_id=int(partner_id), text="⚠️ Stranger left the chat.")
        except:
            pass
    else:
        await update.message.reply_text("⚠️ You're not chatting with anyone.")

# ===============================
# 🔄 Next Chat
@send_typing_action
async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users[user_id]["chatting_with"] = None
    save_users()

    for other_id in users:
        if other_id != user_id and users[other_id].get("chatting_with") is None:
            users[user_id]["chatting_with"] = other_id
            users[other_id]["chatting_with"] = user_id
            save_users()

            await update.message.reply_text("🔗 Connected to a new stranger!")
            await context.bot.send_message(chat_id=int(other_id), text="🔗 Connected to a new stranger!")
            return

    await update.message.reply_text("🔍 Looking for someone to chat with... (Try again after a few seconds)")
# handlers/chat.py - Part 8

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler
from database import users, save_users

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "User"

    if user_id not in users:
        users[user_id] = {
            "id": user_id,
            "name": first_name,
            "partner": None,
            "in_queue": False,
            "active": True,
            "blocked": [],
            "chat_history": []
        }
        save_users()

    await update.message.reply_text(
        f"👋 Hello {first_name}!\n\nWelcome to *Stranger Chat Bot*!\n\nPress /next to start talking with someone anonymously.\n\nUse /stop to leave chat anytime.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

# Register this in main.py
# from handlers.chat import start_command
# app.add_handler(CommandHandler("start", start_command))
# ✅ Part 9: /start command

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "NoUsername"

    # ✅ Profile check
    if user_id not in users:
        await update.message.reply_text("⚠️ Please create your profile first using /menu.")
        return

    is_vip = users[user_id].get("is_vip", False)

    # ✅ VIP or normal welcome message
    if is_vip:
        await update.message.reply_text(
            "💎 Welcome VIP!\nSearching for a match now..."
        )
    else:
        await update.message.reply_text(
            "✅ Welcome back!\nSearching for a match now..."
        )

    # ✅ Start match directly (assumes match_user() function already exists)
    await match_user(update, context)

    # Naya profile banao
    users[user_id] = {
        "id": user_id,
        "username": username,
        "chatting_with": None,
        "is_searching": False
    }

    save_users(users)  # save in database.json

    await update.message.reply_text(
        f"👋 Welcome to Anonymous Connect!\n\n"
        f"You're now part of our stranger chat platform.\n"
        f"Use /next to find a stranger or /stop to leave chat anytime."
    )

# ✅ Part 9: Create Profile
async def create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Anonymous"
    
    # Agar user pehle se exist nahi karta
    if user_id not in users:
        users[user_id] = {
            "name": first_name,
            "chatting_with": None,
            "bio": "Not set yet",
            "gender": "Not set",
            "language": "Not set"
        }
        save_users(users)
        await update.message.reply_text(
            f"👤 Profile created successfully, {first_name}!\nUse /menu to explore more."
        )
    else:
        await update.message.reply_text("✅ Profile already exists. Use /menu to update or view it.")
        
from telegram import ReplyKeyboardMarkup

# ✅ Part 10: /menu command

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📜 Profile", "🎁 Bonus"],
        ["🌐 Translate", "📖 Rules"],
        ["📸 Photo Roulette", "💎 Get VIP"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=False
    )

    await update.message.reply_text("🔘 Choose an option from the menu below:", reply_markup=reply_markup)

# ✅ Part 11: Show Profile (📜 Profile button)
from telegram import ReplyKeyboardMarkup  # already added by you ✅
from telegram.ext import MessageHandler, filters  # Make sure it's imported

async def handle_profile_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users:
        await update.message.reply_text(
            "⚠️ You don't have a profile yet.\nUse /create_profile to make one."
        )
        return

    user = users[user_id]
    name = user.get("name", "Not set")
    gender = user.get("gender", "Not set")
    bio = user.get("bio", "Not set")
    language = user.get("language", "Not set")

    profile_text = (
        f"👤 <b>Your Profile</b>\n"
        f"• 🧑 Name: {name}\n"
        f"• 🚻 Gender: {gender}\n"
        f"• 📝 Bio: {bio}\n"
        f"• 🌐 Language: {language}"
    )

    await update.message.reply_text(profile_text, parse_mode="HTML")

# ✅ Register the button handler (at the bottom of chat.py)
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex("^📜 Profile$"), handle_profile_button)
)

# ✅ Part 12: Handle 🎁 Bonus Button (Diamond-themed)
import random  # make sure this is imported once at top

async def handle_bonus_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bonus_messages = [
        "💎 You found a hidden diamond... but it's fake 😅",
        "🎁 Bonus? Nah bro, real rewards only come with VIP.",
        "👀 Hint: Try pressing 💎 Get VIP to see the future.",
        "✨ Stay active! Diamond Version is coming for legends.",
        "🚫 No bonuses here. Real power is 💎 VIP exclusive."
    ]

    message = random.choice(bonus_messages)
    await update.message.reply_text(message)

# ✅ Register Bonus Button Handler
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex("^🎁 Bonus$"), handle_bonus_button)
)

# ✅ Part 13: Handle 📖 Rules Button

async def handle_rules_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = (
        "<b>📖 Community Rules</b>\n\n"
        "1️⃣ Be respectful — No hate, abuse, or harassment.\n"
        "2️⃣ No spamming or flooding messages 🚫\n"
        "3️⃣ Don't share personal info 🕵️\n"
        "4️⃣ Report suspicious behavior to admins ⚠️\n"
        "5️⃣ Enjoy chatting & make meaningful connections 😄\n\n"
        "🔒 Breaking rules may result in permanent ban.\n"
        "💎 VIPs are also expected to follow all rules."
    )

    await update.message.reply_text(rules_text, parse_mode="HTML")

# ✅ Register Rules Button Handler
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex("^📖 Rules$"), handle_rules_button)
)

# ✅ Part 14: Handle 📸 Photo Roulette Button

import random

async def handle_photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roulette_responses = [
        "📸 Snap a selfie with your current mood and imagine sending it here 😜",
        "👻 If this were real, you would've just sent a pic to a stranger!",
        "🤳 Photo Roulette coming soon in VIP version... maybe with real uploads 👀",
        "📷 Smile! You just got caught by the roulette bot 😆",
        "💡 Imagine a feature where strangers swap one photo blindly... would you try it?"
    ]

    message = random.choice(roulette_responses)
    await update.message.reply_text(message)

# ✅ Register Photo Roulette Button Handler
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex("^📸 Photo Roulette$"), handle_photo_roulette)
)

# ✅ Part 15: Handle 🌐 Translate Button

async def handle_translate_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    translate_message = (
        "🌐 <b>Translation Feature (Coming Soon)</b>\n\n"
        "💬 Chatting with someone who speaks a different language?\n"
        "No worries! Our upcoming Diamond Version will auto-translate messages in real time.\n\n"
        "👀 Supported languages:\n"
        "• English 🇬🇧\n"
        "• Hindi 🇮🇳\n"
        "• Spanish 🇪🇸\n"
        "• French 🇫🇷\n"
        "• And more coming soon!\n\n"
        "💎 This feature will be available only for VIP users."
    )

    await update.message.reply_text(translate_message, parse_mode="HTML")

# ✅ Register Translate Button Handler
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex("^🌐 Translate$"), handle_translate_button)
)

# ✅ Part 16: Handle 💎 Get VIP Button (Final Clean Version)

async def handle_vip_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vip_message = (
        "💎 <b>Upgrade to Diamond VIP</b>\n\n"
        "🚀 Unlock Premium Features:\n"
        "• Verified user chat only 👑\n"
        "• Gender & interest filters ⚙️\n"
        "• Early access to new features ✨\n"
        "• VIP badge on your profile 🔥\n"
        "• Auto-translation 🌐\n"
        "• Zero wait-time for next chats ⏩\n\n"
        "💰 <b>Pricing:</b>\n"
        "• ₹149 / month\n"
        "• ₹10,000 / lifetime access\n\n"
        "📞 <b>Connect Admin</b> to upgrade (Admin ID in bot bio)"
    )

    await update.message.reply_text(vip_message, parse_mode="HTML")

# ✅ Register VIP Button Handler
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex("^💎 Get VIP$"), handle_vip_button)
)

# ✅ Required import at the top (if not already)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ✅ Profile Update Steps
UPDATE_NAME, UPDATE_GENDER, UPDATE_BIO, UPDATE_LANG = range(4)

# ✅ Step 1: Start update
async def start_profile_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Let's update your profile!\n\nWhat is your name?")
    return UPDATE_NAME

# ✅ Step 2: Name
async def update_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("🚻 What is your gender?")
    return UPDATE_GENDER

# ✅ Step 3: Gender
async def update_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    await update.message.reply_text("📝 Write a short bio:")
    return UPDATE_BIO

# ✅ Step 4: Bio
async def update_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bio"] = update.message.text
    await update.message.reply_text("🌐 What is your preferred language?")
    return UPDATE_LANG

# ✅ Step 5: Language & Save
async def update_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data["language"] = update.message.text

    users[user_id] = users.get(user_id, {})
    users[user_id]["name"] = context.user_data["name"]
    users[user_id]["gender"] = context.user_data["gender"]
    users[user_id]["bio"] = context.user_data["bio"]
    users[user_id]["language"] = context.user_data["language"]

    save_users(users)

    await update.message.reply_text("✅ Profile updated successfully!\nUse /menu to continue.")
    return ConversationHandler.END

# ✅ Cancel update
async def cancel_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Profile update cancelled.")
    return ConversationHandler.END

# ✅ Add this at the bottom of handlers/chat.py to register handler
update_profile_conv = ConversationHandler(
    entry_points=[CommandHandler("update_profile", start_profile_update)],
    states={
        UPDATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_name)],
        UPDATE_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_gender)],
        UPDATE_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_bio)],
        UPDATE_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_language)],
    },
    fallbacks=[CommandHandler("cancel", cancel_update)],
)

application.add_handler(update_profile_conv)

# ✅ Required imports
import os
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ✅ Admin ID via Environment Variable
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # ← default fallback, replace if needed

# ✅ Report Step
REPORT_REASON = range(1)

# ✅ Step 1: Start Report
async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚨 Who do you want to report and why?\nPlease describe briefly.\n\n"
        "You can type /cancel to stop anytime."
    )
    return REPORT_REASON

# ✅ Step 2: Receive Reason & Send to Admin
async def handle_report_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = update.message.text

    report_message = (
        f"🚨 <b>New Report Submitted</b>\n\n"
        f"👤 <b>From:</b> {user.first_name} (@{user.username or 'No username'})\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📄 <b>Reason:</b>\n{reason}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=report_message, parse_mode="HTML")
    await update.message.reply_text("✅ Thank you. Your report has been sent to the admin.")
    return ConversationHandler.END

# ✅ Cancel Report
async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Report cancelled.")
    return ConversationHandler.END

# ✅ Register Report Handler (bottom of chat.py)
report_conv = ConversationHandler(
    entry_points=[CommandHandler("report", start_report)],
    states={
        REPORT_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report_reason)],
    },
    fallbacks=[CommandHandler("cancel", cancel_report)],
)

application.add_handler(report_conv)

# ✅ Nickname Generator
import random

EMOJIS = ["🐱", "🦁", "🐼", "🐸", "🦊", "🐵", "🐧", "🐻", "🐯", "🦄", "🐨", "🐤", "🐙", "🦋", "🌸"]
WORDS = ["Tiger", "Panda", "Rose", "Shadow", "Moon", "Storm", "Angel", "Falcon", "Knight", "Ghost", "Flame", "Wolf"]

def generate_nickname():
    emoji = random.choice(EMOJIS)
    word = random.choice(WORDS)
    number = random.randint(100, 999)
    return f"{emoji} {word}_{number}"

# ✅ Call this to assign nickname if not set
def ensure_nickname(user_id):
    if user_id in users and "nickname" not in users[user_id]:
        users[user_id]["nickname"] = generate_nickname()
        save_users(users)

def is_vip(user_id):
    return users.get(user_id, {}).get("is_vip", False)

from telegram.ext import CommandHandler

async def makevip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # ✅ Check if sender is admin
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ You're not authorized to use this command.")
        return

    # ✅ Get target user ID from command argument
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a user ID. Example:\n`/makevip 123456789`", parse_mode="Markdown")
        return

    target_id = context.args[0]

    if target_id in users:
        users[target_id]["is_vip"] = True
        save_users(users)
        await update.message.reply_text(f"✅ User `{target_id}` has been promoted to VIP!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ User ID not found in database.")

from telegram.ext import CommandHandler

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        await update.message.reply_text("❌ You don't have a profile yet. Use /menu to create one.")
        return

    user = users[user_id]
    
    name = user.get("name", "Anonymous")
    nickname = user.get("nickname", "Not set")
    bio = user.get("bio", "Not set")
    gender = user.get("gender", "Not set")
    language = user.get("language", "Not set")
    is_vip = user.get("is_vip", False)

    vip_status = "💎 VIP" if is_vip else "🔓 Free User"

    profile_text = (
        f"👤 *Your Profile*\n"
        f"🆔 Name: `{name}`\n"
        f"🌟 Nickname: `{nickname}`\n"
        f"📖 Bio: `{bio}`\n"
        f"🚻 Gender: `{gender}`\n"
        f"🌐 Language: `{language}`\n"
        f"💼 Status: {vip_status}"
    )

    await update.message.reply_text(profile_text, parse_mode="Markdown")

async def setbio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        await update.message.reply_text("❌ You don't have a profile yet. Use /menu to create one.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please enter a bio. Example:\n`/setbio I love music.`", parse_mode="Markdown")
        return

    bio = " ".join(context.args)
    users[user_id]["bio"] = bio
    save_users(users)

    await update.message.reply_text("✅ Your bio has been updated!")

async def setgender_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        await update.message.reply_text("❌ You don't have a profile yet. Use /menu to create one.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please enter a gender. Example:\n`/setgender Male`", parse_mode="Markdown")
        return

    gender = context.args[0].capitalize()
    users[user_id]["gender"] = gender
    save_users(users)

    await update.message.reply_text("✅ Your gender has been updated!")

async def setlanguage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        await update.message.reply_text("❌ You don't have a profile yet. Use /menu to create one.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please enter a language. Example:\n`/setlanguage English`", parse_mode="Markdown")
        return

    language = context.args[0].capitalize()
    users[user_id]["language"] = language
    save_users(users)

    await update.message.reply_text("✅ Your language has been updated!")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in users:
        await update.message.reply_text("❌ You don't have a profile yet. Use /menu to create one.")
        return

    # Check if user is in a chat
    partner_id = users[user_id].get("chatting_with")
    
    if not partner_id:
        await update.message.reply_text("⚠️ You are not in a chat to report anyone.")
        return

    # Notify user
    await update.message.reply_text("🚨 The user has been reported. Thank you for helping us keep the community safe.")

    # Notify admin
    try:
        report_text = (
            f"🚨 *User Reported!*\n\n"
            f"👤 *Reported User ID:* `{partner_id}`\n"
            f"🙋 *Reported By:* `{user_id}`"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=report_text, parse_mode="Markdown")
    except Exception as e:
        print(f"[!] Failed to send report to admin: {e}")

from telegram.ext import CommandHandler

def register_chat_handlers(app):
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("next", next_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("create_profile", create_profile))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("setbio", setbio_command))
    app.add_handler(CommandHandler("setgender", setgender_command))
    app.add_handler(CommandHandler("setlanguage", setlanguage_command))
    app.add_handler(CommandHandler("makevip", makevip_command))
    app.add_handler(CommandHandler("report", report_command))
