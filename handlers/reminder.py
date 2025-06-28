from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import time
from database import users, save_users

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /remindme <minutes> <message>")

    try:
        mins = int(context.args[0])
        text = " ".join(context.args[1:])
        remind_at = time.time() + (mins * 60)

        users.setdefault(user_id, {}).setdefault("reminders", []).append({
            "time": remind_at,
            "text": text
        })
        save_users(users)

        await update.message.reply_text(f"✅ Reminder set in {mins} minutes.")
    except:
        await update.message.reply_text("❌ Invalid input. Use: /remindme <minutes> <message>")

# Optional: Disable daily quotes
async def toggle_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    flag = users.setdefault(user_id, {}).get("daily_quote", True)
    users[user_id]["daily_quote"] = not flag
    save_users(users)

    status = "ON ✅" if not flag else "OFF ❌"
    await update.message.reply_text(f"📩 Daily quotes turned *{status}*", parse_mode="Markdown")

def register_reminder_handler(app):
    app.add_handler(CommandHandler("remindme", set_reminder))
    app.add_handler(CommandHandler("togglequotes", toggle_quotes))
