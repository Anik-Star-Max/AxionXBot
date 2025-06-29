from telegram import Update
from telegram.ext import ContextTypes
from database import users, save_users

ASK_NAME, ASK_AGE, ASK_GENDER, CHAT = range(4)

# Step 1 - Ask name
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users[user_id] = {"name": None, "age": None, "gender": None, "chatting_with": None}
    save_users()
    await update.message.reply_text("👋 Welcome! Please enter your name:")
    return ASK_NAME

# Step 2 - Save name and ask age
async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users[user_id]["name"] = update.message.text.strip()
    save_users()
    await update.message.reply_text("📅 Great! Now enter your age:")
    return ASK_AGE

# Step 3 - Save age and ask gender
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users[user_id]["age"] = update.message.text.strip()
    save_users()
    await update.message.reply_text("🚻 Last step, please enter your gender (Male/Female/Other):")
    return ASK_GENDER

# Step 4 - Save gender and match
async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users[user_id]["gender"] = update.message.text.strip()
    users[user_id]["chatting_with"] = None
    save_users()

    # Try to find partner
    for uid, data in users.items():
        if uid != user_id and data.get("chatting_with") is None:
            users[user_id]["chatting_with"] = uid
            users[uid]["chatting_with"] = user_id
            save_users()

            await context.bot.send_message(chat_id=int(uid), text="🟢 You are now connected to a stranger. Say hi!")
            await context.bot.send_message(chat_id=int(user_id), text="🟢 You are now connected to a stranger. Say hi!")
            return CHAT

    await update.message.reply_text("⏳ No strangers available now. Please wait...")
    return CHAT

# Relay messages
async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chatting_with")

    if partner_id and partner_id in users:
        await context.bot.send_message(chat_id=int(partner_id), text=update.message.text)
    else:
        await update.message.reply_text("❌ You're not chatting with anyone. Use /next to connect.")

# /next command
async def next_stranger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chatting_with")

    if partner_id:
        users[user_id]["chatting_with"] = None
        users[partner_id]["chatting_with"] = None
        save_users()
        await context.bot.send_message(chat_id=int(partner_id), text="🔁 Stranger left the chat. Use /next to find someone new.")
        await update.message.reply_text("🔁 You left the chat. Finding new stranger...")
    else:
        await update.message.reply_text("🔍 Searching for a stranger...")

    return await find_partner(update, context)

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
        await update.message.reply_text("🚫 You're not in any chat.")
    return ConversationHandler.END
