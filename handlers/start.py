# handlers/start.py

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from database import users, save_users
import random

ASK_NAME, ASK_AGE, ASK_GENDER, CHAT = range(4)

def register_start_handler(app):

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat)],
        },
        fallbacks=[
            CommandHandler("next", next_stranger),
            CommandHandler("stop", stop_chat)
        ],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("next", next_stranger))
    app.add_handler(CommandHandler("stop", stop_chat))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in users:
        await update.message.reply_text("Welcome back! Finding a stranger for you...")
        await find_partner(update, context)
        return CHAT
    else:
        await update.message.reply_text("👋 Welcome! Let's create your profile first.\nWhat's your name?")
        return ASK_NAME
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Great! Now tell me your age:")
    return ASK_AGE


async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age = update.message.text.strip()
    if not age.isdigit():
        await update.message.reply_text("Please enter a valid age (numbers only):")
        return ASK_AGE

    context.user_data["age"] = int(age)
    await update.message.reply_text(
        "Awesome! What's your gender?",
        reply_markup=ReplyKeyboardMarkup(
            [["Male", "Female", "Other"]], one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return ASK_GENDER


async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.strip()
    if gender not in ["Male", "Female", "Other"]:
        await update.message.reply_text("Please choose from Male, Female, or Other:")
        return ASK_GENDER

    user_id = str(update.effective_user.id)
    users[user_id] = {
        "name": context.user_data["name"],
        "age": context.user_data["age"],
        "gender": gender,
        "chatting_with": None,
    }
    save_users()
    await update.message.reply_text("✅ Profile saved! Searching for a stranger...")
    await find_partner(update, context)
    return CHAT
# Match users
async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    for uid, data in users.items():
        if uid != user_id and data.get("chatting_with") is None:
            # Match found
            users[user_id]["chatting_with"] = uid
            users[uid]["chatting_with"] = user_id
            save_users()

            await context.bot.send_message(chat_id=int(uid), text="🎯 You are now connected to a stranger. Say hi!")
            await context.bot.send_message(chat_id=int(user_id), text="🎯 You are now connected to a stranger. Say hi!")
            return

    await update.message.reply_text("😓 No stranger available right now. Please wait...")

# Handle chat messages between strangers
async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = str(update.effective_user.id)
    partner_id = users.get(sender_id, {}).get("chatting_with")

    if partner_id and partner_id in users:
        await context.bot.send_message(chat_id=int(partner_id), text=update.message.text)
    else:
        await update.message.reply_text("❌ You're not connected to anyone. Use /next to find a stranger.")

# /next command
async def next_stranger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chatting_with")

    if partner_id:
        users[user_id]["chatting_with"] = None
        users[partner_id]["chatting_with"] = None
        save_users()

        await context.bot.send_message(chat_id=int(partner_id), text="🔁 Stranger left the chat. Use /next to find someone new.")
        await update.message.reply_text("🔁 You left the chat. Searching for a new stranger...")
    else:
        await update.message.reply_text("🔎 Searching for a stranger...")

    await find_partner(update, context)

# /stop command
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chatting_with")

    if partner_id:
        users[user_id]["chatting_with"] = None
        users[partner_id]["chatting_with"] = None
        save_users()

        await context.bot.send_message(chat_id=int(partner_id), text="🛑 Stranger ended the chat.")
        await update.message.reply_text("🛑 You ended the chat.")
    else:
        await update.message.reply_text("❌ You're not chatting with anyone.")
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
)

from database import users, save_users
from .start_logic import ask_name, ask_age, ask_gender, handle_chat, find_partner, next_stranger, stop_chat

ASK_NAME, ASK_AGE, ASK_GENDER, CHAT = range(4)

def register_start_handler(app):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", ask_name)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat),
                CommandHandler("next", next_stranger),
                CommandHandler("stop", stop_chat),
            ],
        },
        fallbacks=[CommandHandler("stop", stop_chat)],
    )
    app.add_handler(conv_handler)
