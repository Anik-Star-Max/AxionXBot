from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
import json
from datetime import datetime
from database import load_users, save_users

# Load and save user data
USERS_DB = "users.json"
users = load_users()

# Constants for ConversationHandler steps
ASK_NAME, ASK_AGE, ASK_FEEDBACK = range(3)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "registered": str(datetime.now()),
            "feedback": [],
        }
        save_users(users)
    await update.message.reply_text(
        f"Hi {update.effective_user.first_name}!\nWelcome to our Telegram bot. Use /help to see commands."
    )

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start the bot\n"
        "/register - Register yourself\n"
        "/feedback - Give your feedback\n"
        "/profile - View your profile"
    )

# /profile command
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in users:
        user_data = users[user_id]
        await update.message.reply_text(
            f"👤 Profile:\n"
            f"Name: {user_data.get('first_name')}\n"
            f"Username: @{user_data.get('username')}\n"
            f"Registered on: {user_data.get('registered')}"
        )
    else:
        await update.message.reply_text("❌ You are not registered. Use /start to register.")

# /register command with conversation
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 What's your full name?")
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("🔢 What's your age?")
    return ASK_AGE

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("💬 Any feedback for us?")
    return ASK_FEEDBACK

async def ask_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    feedback = update.message.text
    if user_id in users:
        users[user_id]["feedback"].append(feedback)
        save_users(users)
    await update.message.reply_text("✅ Thanks for registering and your feedback!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Registration cancelled.")
    return ConversationHandler.END

# Inline buttons (Example)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "like":
        await query.edit_message_text("You liked this!")
    elif query.data == "dislike":
        await query.edit_message_text("You disliked this.")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))

    app.add_handler(CallbackQueryHandler(button_handler))

    # Register Conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_feedback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
# Broadcast message to all users (Admin only)
ADMIN_IDS = ["123456789", "987654321"]  # Replace with real admin IDs

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if context.args:
        message = " ".join(context.args)
        count = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=message)
                count += 1
            except:
                continue
        await update.message.reply_text(f"✅ Message sent to {count} users.")
    else:
        await update.message.reply_text("⚠️ Please provide a message to broadcast.")

# Send custom button menu (Example command)
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👍 Like", callback_data="like")],
        [InlineKeyboardButton("👎 Dislike", callback_data="dislike")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Do you like this bot?", reply_markup=reply_markup)

# Feedback viewer for admin
async def view_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    msg = ""
    for uid, data in users.items():
        feedbacks = data.get("feedback", [])
        if feedbacks:
            msg += f"🧑 {data.get('first_name')} (@{data.get('username')}):\n"
            for fb in feedbacks:
                msg += f"   - {fb}\n"
            msg += "\n"

    if msg:
        await update.message.reply_text(f"📝 Feedbacks:\n\n{msg}")
    else:
        await update.message.reply_text("No feedback found.")

# Simple /about command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *About This Bot*\n\n"
        "Created to demonstrate Telegram bot features including:\n"
        "• User registration\n"
        "• Inline buttons\n"
        "• Feedback system\n"
        "• Admin broadcast\n"
        "• and more...",
        parse_mode="Markdown"
    )

# Command for deleting a user (Admin only)
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if context.args:
        target_id = context.args[0]
        if target_id in users:
            del users[target_id]
            save_users(users)
            await update.message.reply_text(f"✅ User {target_id} deleted.")
        else:
            await update.message.reply_text("⚠️ User not found.")
    else:
        await update.message.reply_text("Please provide a user ID to delete.")

# Register more handlers (continue from previous register_handlers function)
def register_more_handlers(app):
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("feedbacks", view_feedback))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("deleteuser", delete_user))
# Daily quote feature (Example feature for engagement)
import random

QUOTES = [
    "Believe in yourself and all that you are.",
    "Push yourself, because no one else is going to do it for you.",
    "Dream it. Wish it. Do it.",
    "Great things never come from comfort zones.",
    "Success doesn’t just find you. You have to go out and get it."
]

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(QUOTES)
    await update.message.reply_text(f"💡 Quote of the Day:\n\n_{q}_", parse_mode="Markdown")

# Admin command to add new quote
async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if context.args:
        new_quote = " ".join(context.args)
        QUOTES.append(new_quote)
        await update.message.reply_text("✅ Quote added.")
    else:
        await update.message.reply_text("⚠️ Please provide a quote to add.")

# Register quote commands
def register_quote_handlers(app):
    app.add_handler(CommandHandler("quote", quote))
    app.add_handler(CommandHandler("addquote", add_quote))

# Custom keyboard menu (example for regular users)
async def keyboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📋 Profile"), KeyboardButton("📤 Feedback")],
        [KeyboardButton("💡 Quote"), KeyboardButton("❓ Help")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

# Handle button presses from custom keyboard
async def keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Profile" in text:
        await profile(update, context)
    elif "Feedback" in text:
        await update.message.reply_text("Use /register to give feedback.")
    elif "Quote" in text:
        await quote(update, context)
    elif "Help" in text:
        await help_command(update, context)
    else:
        await update.message.reply_text("Unknown option.")

def register_keyboard_handlers(app):
    app.add_handler(CommandHandler("menu2", keyboard_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyboard_handler))

# Full registration of all handlers in one place
def register_all_handlers(app):
    register_handlers(app)
    register_more_handlers(app)
    register_quote_handlers(app)
    register_keyboard_handlers(app)
# Logging all messages (Optional: For admin monitoring or stats)
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Error handler to catch exceptions
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        await update.message.reply_text("⚠️ An unexpected error occurred. Please try again later.")
    except:
        pass

# Register error handler
def register_error_handler(app):
    app.add_error_handler(error_handler)

# Inline menu with multiple buttons (More advanced)
async def inline_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📝 Register", callback_data="inline_register"),
            InlineKeyboardButton("👤 Profile", callback_data="inline_profile"),
        ],
        [
            InlineKeyboardButton("💬 Feedback", callback_data="inline_feedback"),
            InlineKeyboardButton("💡 Quote", callback_data="inline_quote"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option below:", reply_markup=reply_markup)

async def inline_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "inline_register":
        await query.edit_message_text("Use /register to start the registration process.")
    elif data == "inline_profile":
        await profile(update, context)
    elif data == "inline_feedback":
        await query.edit_message_text("Use /register to submit feedback.")
    elif data == "inline_quote":
        await quote(update, context)
    else:
        await query.edit_message_text("Invalid option.")

def register_inline_menu_handlers(app):
    app.add_handler(CommandHandler("inline", inline_options))
    app.add_handler(CallbackQueryHandler(inline_menu_handler, pattern="^inline_"))
# Admin panel menu (inline based)
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access Denied. Admins only.")
        return

    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🧾 View Feedbacks", callback_data="admin_feedbacks")],
        [InlineKeyboardButton("🗑 Delete User", callback_data="admin_delete")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Admin Panel", reply_markup=reply_markup)

async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)

    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ You are not authorized.")
        return

    if data == "admin_broadcast":
        await query.edit_message_text("Use /broadcast <message> to send broadcast.")
    elif data == "admin_feedbacks":
        await query.edit_message_text("Use /feedbacks to view all user feedbacks.")
    elif data == "admin_delete":
        await query.edit_message_text("Use /deleteuser <user_id> to delete any user.")
    else:
        await query.edit_message_text("Unknown admin action.")

def register_admin_panel(app):
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_panel_handler, pattern="^admin_"))

# Stats command for admins
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to view stats.")
        return

    total_users = len(users)
    feedback_count = sum(len(data.get("feedback", [])) for data in users.values())
    await update.message.reply_text(
        f"📊 Bot Stats:\n\n"
        f"👥 Total Users: {total_users}\n"
        f"💬 Total Feedbacks: {feedback_count}"
    )

def register_stat_handler(app):
    app.add_handler(CommandHandler("stats", stats))
# Admin-only command to export all user data as JSON file
import os
import tempfile

async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.json') as f:
        json.dump(users, f, indent=2)
        temp_path = f.name

    with open(temp_path, 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename='users_backup.json')

    os.remove(temp_path)

def register_export_handler(app):
    app.add_handler(CommandHandler("export", export_users))

# Command for resetting all feedbacks (admin only)
async def reset_feedbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    for uid in users:
        users[uid]["feedback"] = []
    save_users(users)
    await update.message.reply_text("✅ All feedbacks have been cleared.")

def register_reset_handler(app):
    app.add_handler(CommandHandler("resetfeedbacks", reset_feedbacks))

# Master function to register everything
def register_everything(app):
    register_all_handlers(app)
    register_admin_panel(app)
    register_stat_handler(app)
    register_export_handler(app)
    register_reset_handler(app)
    register_error_handler(app)
# Utility: Format user info
def format_user(user_id, user_data):
    return (
        f"🆔 ID: {user_id}\n"
        f"👤 Name: {user_data.get('first_name', 'N/A')}\n"
        f"🔗 Username: @{user_data.get('username', 'N/A')}\n"
        f"📅 Registered: {user_data.get('registered', 'N/A')}\n"
        f"💬 Feedbacks: {len(user_data.get('feedback', []))}"
    )

# Inline user search (admin only)
async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if not context.args:
        await update.message.reply_text("🔍 Usage: /search <user_id>")
        return

    target_id = context.args[0]
    if target_id in users:
        msg = format_user(target_id, users[target_id])
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ User not found.")

def register_search_handler(app):
    app.add_handler(CommandHandler("search", search_user))

# Final master function to connect all register_* in one call
def setup_all_handlers(app):
    register_everything(app)
    register_search_handler(app)
# Additional imports for advanced features
from telegram.constants import ChatAction
from telegram.error import Forbidden
from telegram.helpers import mention_html
from telegram.ext.filters import PHOTO, VIDEO

# Warning system
WARN_LIMIT = 3
if "warnings" not in users:
    for uid in users:
        users[uid]["warnings"] = 0
save_users(users)

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /warn <user_id>")

    target_id = context.args[0]
    if target_id not in users:
        return await update.message.reply_text("User not found.")

    users[target_id]["warnings"] += 1
    save_users(users)

    warns = users[target_id]["warnings"]
    await update.message.reply_text(f"⚠️ User {target_id} warned. Total warnings: {warns}")

    try:
        await context.bot.send_message(chat_id=int(target_id),
                                       text=f"⚠️ You have been warned by the admin.\nWarnings: {warns}/{WARN_LIMIT}")
    except:
        pass

    if warns >= WARN_LIMIT:
        await ban_user_logic(context.bot, target_id, reason="Exceeded warning limit.")

async def reset_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")
    
    if not context.args:
        return await update.message.reply_text("Usage: /resetwarn <user_id>")
    
    uid = context.args[0]
    if uid in users:
        users[uid]["warnings"] = 0
        save_users(users)
        await update.message.reply_text("✅ Warnings reset.")
    else:
        await update.message.reply_text("User not found.")

async def ban_user_logic(bot, user_id, reason=""):
    users[user_id]["banned"] = True
    save_users(users)
    try:
        await bot.send_message(chat_id=int(user_id), text=f"🚫 You have been banned.\nReason: {reason}")
    except:
        pass

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /unban <user_id>")
    
    uid = context.args[0]
    if uid in users and users[uid].get("banned"):
        users[uid]["banned"] = False
        users[uid]["warnings"] = 0
        save_users(users)
        await update.message.reply_text(f"✅ User {uid} unbanned.")
    else:
        await update.message.reply_text("User not found or not banned.")

# Check ban on every message
async def check_ban_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if users.get(user_id, {}).get("banned"):
        try:
            await update.message.reply_text("⛔ You are banned from using this bot.")
        except:
            pass
        return False
    return True
# Broadcast with text/photo/video
async def advanced_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = str(update.effective_user.id)
    if sender_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    if not context.args:
        return await update.message.reply_text("Usage: /bcast <message>")

    message_text = " ".join(context.args)
    success, fail = 0, 0

    for uid in users.copy():
        if users[uid].get("banned"):
            continue
        try:
            await context.bot.send_chat_action(chat_id=int(uid), action=ChatAction.TYPING)
            await context.bot.send_message(chat_id=int(uid), text=message_text)
            success += 1
        except Forbidden:
            del users[uid]  # User blocked or removed the bot
            fail += 1
        except:
            fail += 1

    save_users(users)
    await update.message.reply_text(f"✅ Broadcast sent!\n✔️ Delivered: {success}\n❌ Failed: {fail}")

# Broadcast image
async def broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    if not update.message.photo:
        return await update.message.reply_text("⚠️ Send an image with a caption using /bphoto <caption>")

    caption = update.message.caption or "📢 New update!"
    file_id = update.message.photo[-1].file_id

    success, fail = 0, 0
    for uid in users.copy():
        if users[uid].get("banned"):
            continue
        try:
            await context.bot.send_photo(chat_id=int(uid), photo=file_id, caption=caption)
            success += 1
        except Forbidden:
            del users[uid]
            fail += 1
        except:
            fail += 1

    save_users(users)
    await update.message.reply_text(f"📸 Photo broadcast done!\n✔️: {success}, ❌: {fail}")

# Broadcast video
async def broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    if not update.message.video:
        return await update.message.reply_text("⚠️ Send a video with a caption using /bvideo <caption>")

    caption = update.message.caption or "📢 New video alert!"
    file_id = update.message.video.file_id

    success, fail = 0, 0
    for uid in users.copy():
        if users[uid].get("banned"):
            continue
        try:
            await context.bot.send_video(chat_id=int(uid), video=file_id, caption=caption)
            success += 1
        except Forbidden:
            del users[uid]
            fail += 1
        except:
            fail += 1

    save_users(users)
    await update.message.reply_text(f"🎬 Video broadcast done!\n✔️: {success}, ❌: {fail}")

# Register these handlers
def register_broadcast_media(app):
    app.add_handler(CommandHandler("bcast", advanced_broadcast))
    app.add_handler(MessageHandler(filters.PHOTO & filters.Caption(), broadcast_photo))
    app.add_handler(MessageHandler(filters.VIDEO & filters.Caption(), broadcast_video))
# List all users (paginated)
USERS_PER_PAGE = 10

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    total = len(users)
    pages = (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE

    start = (page - 1) * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    user_slice = list(users.items())[start:end]

    if not user_slice:
        return await update.message.reply_text("⚠️ No users on this page.")

    text = f"📋 *User List* (Page {page}/{pages})\n\n"
    for uid, data in user_slice:
        text += f"🆔 `{uid}` | {data.get('first_name', 'N/A')} | @{data.get('username', 'N/A')}\n"

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"users_{page - 1}"))
    if page < pages:
        buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"users_{page + 1}"))

    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# Callback for user list pagination
async def paginate_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("users_"):
        return

    page = int(data.split("_")[1])
    context.args = [str(page)]
    fake_update = Update(update.update_id, message=query.message)
    fake_update.effective_user = query.from_user
    await list_users(fake_update, context)

# Stats by feedback count
async def top_feedback_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Not allowed")

    sorted_users = sorted(users.items(), key=lambda x: len(x[1].get("feedback", [])), reverse=True)
    top = sorted_users[:10]

    if not top:
        return await update.message.reply_text("No feedback data available.")

    text = "🏆 *Top Feedback Givers:*\n\n"
    for uid, data in top:
        count = len(data.get("feedback", []))
        name = data.get("first_name", 'N/A')
        uname = f"@{data.get('username')}" if data.get("username") else "No username"
        text += f"👤 {name} ({uname}) — {count} feedbacks\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# Register pagination and user list
def register_user_admin_tools(app):
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CallbackQueryHandler(paginate_users, pattern=r"^users_\d+"))
    app.add_handler(CommandHandler("topfeedback", top_feedback_users))
import csv
from datetime import datetime

# Export feedbacks to CSV
async def export_feedback_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    filename = f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["User ID", "Username", "Name", "Feedback"])

        for uid, data in users.items():
            feedbacks = data.get("feedback", [])
            for fb in feedbacks:
                writer.writerow([
                    uid,
                    data.get("username", "N/A"),
                    data.get("first_name", "N/A"),
                    fb
                ])

    with open(filename, "rb") as file:
        await update.message.reply_document(document=file, filename=filename)

    os.remove(filename)

# Add internal admin note to user
async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Not allowed.")

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /addnote <user_id> <note text>")

    target_id = context.args[0]
    note = " ".join(context.args[1:])
    
    if target_id not in users:
        return await update.message.reply_text("User not found.")

    users[target_id]["note"] = note
    save_users(users)
    await update.message.reply_text(f"📝 Note added to user {target_id}.")

# View a user's note
async def view_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Not allowed.")

    if not context.args:
        return await update.message.reply_text("Usage: /note <user_id>")

    uid = context.args[0]
    if uid not in users:
        return await update.message.reply_text("User not found.")

    note = users[uid].get("note", None)
    if note:
        await update.message.reply_text(f"🧾 Note for {uid}: {note}")
    else:
        await update.message.reply_text("No note found for this user.")

# Reply to feedback (send DM to user)
async def reply_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized.")

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /reply <user_id> <message>")

    uid = context.args[0]
    msg = " ".join(context.args[1:])

    if uid not in users:
        return await update.message.reply_text("User not found.")

    try:
        await context.bot.send_message(chat_id=int(uid), text=f"📬 *Reply from Admin:*\n\n{msg}", parse_mode="Markdown")
        await update.message.reply_text("✅ Reply sent.")
    except:
        await update.message.reply_text("⚠️ Could not send message.")

# Register admin utilities
def register_admin_utilities(app):
    app.add_handler(CommandHandler("exportcsv", export_feedback_csv))
    app.add_handler(CommandHandler("addnote", add_note))
    app.add_handler(CommandHandler("note", view_note))
    app.add_handler(CommandHandler("reply", reply_feedback))
from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

scheduler = AsyncIOScheduler()

# Daily quote message to all users at fixed time
async def send_daily_quote(context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(QUOTES)
    for uid in users.copy():
        if users[uid].get("banned"):
            continue
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"🌞 *Good Morning!*\n\n💡 {quote}", parse_mode="Markdown")
        except Forbidden:
            del users[uid]
        except:
            pass
    save_users(users)

# Reminder system
reminders = {}

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /remind <minutes> <message>")

    try:
        mins = int(context.args[0])
        msg = " ".join(context.args[1:])
        await update.message.reply_text(f"⏳ Reminder set for {mins} minutes from now!")

        async def send_reminder():
            await context.bot.send_message(chat_id=int(uid), text=f"🔔 Reminder:\n{msg}")

        scheduler.add_job(send_reminder, "date", run_date=datetime.now() + timedelta(minutes=mins))
    except:
        await update.message.reply_text("❌ Invalid time.")

# Auto message memory (trigger words)
trigger_memory = {
    "sad": "💙 Stay strong, better days are coming.",
    "help": "🆘 Type /help to get support options.",
    "lost": "🌫 Sometimes getting lost is how we find ourselves."
}

async def auto_memory_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    for keyword, response in trigger_memory.items():
        if keyword in text:
            await update.message.reply_text(response)
            break

# Schedule the daily quote (runs at 9:00 AM daily)
def start_daily_schedule(app: Application):
    scheduler.add_job(send_daily_quote, "cron", hour=9, minute=0, args=[app.bot])
    scheduler.start()

# Register reminder and memory
def register_auto_utilities(app):
    app.add_handler(CommandHandler("remind", set_reminder))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_memory_trigger))
# Help topics
HELP_TOPICS = {
    "register": "📝 Use /register to register yourself in the system.",
    "feedback": "💬 Use /register again to send us feedback anytime.",
    "profile": "👤 Use /profile to view your information.",
    "quote": "💡 Use /quote to get daily motivational quotes.",
    "menu": "📱 Use /menu2 to access simple options via buttons.",
    "admin": "⚙️ Admins have access to /admin panel and other moderation tools."
}

HELP_PER_PAGE = 3

async def help_paginated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    keys = list(HELP_TOPICS.keys())
    total_pages = (len(keys) + HELP_PER_PAGE - 1) // HELP_PER_PAGE

    start = (page - 1) * HELP_PER_PAGE
    end = start + HELP_PER_PAGE
    page_keys = keys[start:end]

    text = f"📖 *Help Menu* (Page {page}/{total_pages})\n\n"
    for key in page_keys:
        text += f"🔹 /{key} — {HELP_TOPICS[key]}\n"

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"help_{page - 1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"help_{page + 1}"))

    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith("help_"):
        return

    page = int(data.split("_")[1])
    context.args = [str(page)]
    fake_update = Update(update.update_id, message=query.message)
    fake_update.effective_user = query.from_user
    await help_paginated(fake_update, context)

# Search help topics
async def search_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /helpsearch <keyword>")

    keyword = context.args[0].lower()
    matches = [f"/{k} — {v}" for k, v in HELP_TOPICS.items() if keyword in k or keyword in v.lower()]
    
    if matches:
        await update.message.reply_text("🔍 *Search Results:*\n\n" + "\n".join(matches), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ No help topics matched your search.")

# Register help system
def register_help_system(app):
    app.add_handler(CommandHandler("help", help_paginated))
    app.add_handler(CallbackQueryHandler(help_callback, pattern=r"^help_\d+"))
    app.add_handler(CommandHandler("helpsearch", search_help))
# Dynamic inline button system
async def link_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Open SMC Book", url="https://yourlink.com/smc")],
        [InlineKeyboardButton("📷 Visit Instagram", url="https://instagram.com/tradexus")],
        [InlineKeyboardButton("🚀 Learn More", callback_data="learn_more")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👇 Tap any button below:", reply_markup=reply_markup)

async def handle_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "learn_more":
        await query.edit_message_text("🚀 You're on your journey to becoming a trading pro!")

# Per-user keyboard lock/unlock
if "keyboard_lock" not in users:
    for uid in users:
        users[uid]["keyboard_lock"] = False
save_users(users)

async def toggle_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Not allowed")

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /keyboard <user_id> <lock/unlock>")

    target_id = context.args[0]
    action = context.args[1].lower()

    if target_id not in users:
        return await update.message.reply_text("User not found.")

    if action == "lock":
        users[target_id]["keyboard_lock"] = True
        msg = "🔒 Keyboard locked."
    elif action == "unlock":
        users[target_id]["keyboard_lock"] = False
        msg = "🔓 Keyboard unlocked."
    else:
        msg = "⚠️ Invalid action. Use lock/unlock."

    save_users(users)
    await update.message.reply_text(msg)

# Middleware to block keyboard-based replies if locked
async def keyboard_blocker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if users.get(user_id, {}).get("keyboard_lock"):
        await update.message.reply_text("🚫 You are restricted from using buttons.")
        return False
    return True

# Register dynamic and control handlers
def register_button_and_keyboard_control(app):
    app.add_handler(CommandHandler("links", link_buttons))
    app.add_handler(CallbackQueryHandler(handle_inline_callback, pattern="^learn_more$"))
    app.add_handler(CommandHandler("keyboard", toggle_keyboard))
# Error handler to catch uncaught exceptions
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger = logging.getLogger(__name__)
    logger.error("Exception while handling update:", exc_info=context.error)

    if update and isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text("⚠️ An unexpected error occurred. Please try again later.")
        except:
            pass

# Shutdown cleanup
async def shutdown_handler(app: Application):
    logger = logging.getLogger(__name__)
    logger.info("Bot is shutting down. Saving user data...")
    save_users(users)
    logger.info("✅ Data saved.")

# Register ALL handlers in one go
def register_all_handlers(app: Application):
    register_user_commands(app)
    register_feedback_handler(app)
    register_admin_panel(app)
    register_stat_handler(app)
    register_export_handler(app)
    register_reset_handler(app)
    register_search_handler(app)
    register_broadcast_media(app)
    register_user_admin_tools(app)
    register_admin_utilities(app)
    register_auto_utilities(app)
    register_help_system(app)
    register_button_and_keyboard_control(app)

    # Middleware & filters
    app.add_handler(MessageHandler(filters.ALL, keyboard_blocker), group=0)

    # Error handling
    app.add_error_handler(error_handler)
