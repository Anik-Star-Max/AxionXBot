from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
import random
from database import users, save_users

# Sad/emotional triggers
TRIGGERS = [
    "sad", "alone", "broken", "pov", "depressed", "leave", "pain", "dark", "end", "cry", "miss", "she", "he", "love"
]

# Emotional auto replies
RESPONSES = [
    "💔 Sometimes, silence is the loudest scream.",
    "🌑 You smiled, but I saw the pain in your eyes.",
    "😞 Not everyone you lose is a loss. Some were lessons.",
    "🕯 You gave them light, they left you in darkness.",
    "📖 POV: You're tired of being strong.",
    "🌪 Maybe you're not broken, just bent in silence.",
    "🌒 Some nights feel longer than they should...",
    "🖤 You mattered. Even if they made you feel like you didn’t."
]

# Enable or disable AI reply per user
for uid in users:
    users[uid].setdefault("ai_reply", True)
save_users(users)

# Toggle command
async def toggle_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = users.setdefault(user_id, {})

    if len(context.args) == 0:
        status = "ON ✅" if user_data.get("ai_reply", True) else "OFF ❌"
        return await update.message.reply_text(f"🤖 AI Reply is currently *{status}*", parse_mode="Markdown")

    arg = context.args[0].lower()
    if arg == "off":
        user_data["ai_reply"] = False
        msg = "🤖 AI replies *disabled* for you."
    elif arg == "on":
        user_data["ai_reply"] = True
        msg = "🤖 AI replies *enabled* for you."
    else:
        msg = "Usage: /ai on OR /ai off"

    save_users(users)
    await update.message.reply_text(msg, parse_mode="Markdown")

# Auto smart emotional reply
async def smart_ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    message = update.message.text.lower()

    if not users.get(user_id, {}).get("ai_reply", True):
        return  # user has disabled AI

    if any(trigger in message for trigger in TRIGGERS):
        response = random.choice(RESPONSES)
        await update.message.reply_text(response)

# Register AI system
def register_ai_reply(app):
    app.add_handler(CommandHandler("ai", toggle_ai))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), smart_ai_reply), group=3)
