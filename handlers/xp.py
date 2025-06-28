from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import users, save_users

# Constants
XP_PER_MESSAGE = 2
LEVEL_THRESHOLDS = [0, 10, 25, 50, 100, 200, 400, 800, 1600, 3200]  # XP required per level

def get_level(xp: int) -> int:
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp < threshold:
            return i
    return len(LEVEL_THRESHOLDS)

# Middleware: Grant XP on any message
async def grant_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user is None or user.is_bot:
        return

    user_id = str(user.id)
    users.setdefault(user_id, {})
    users[user_id]["xp"] = users[user_id].get("xp", 0) + XP_PER_MESSAGE
    save_users(users)

# Show user's level and XP
async def show_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = users.get(user_id, {})
    xp = user_data.get("xp", 0)
    level = get_level(xp)

    await update.message.reply_text(
        f"⭐ XP: {xp}\n🎯 Level: {level}"
    )

# Show leaderboard
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = sorted(users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

    msg = "🏆 *Top 10 Users by XP:*\n\n"
    for i, (uid, data) in enumerate(top_users, start=1):
        name = data.get("first_name", "Unknown")
        xp = data.get("xp", 0)
        level = get_level(xp)
        msg += f"{i}. {name} — {xp} XP (Level {level})\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# Register XP handlers
def register_xp_handler(app):
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), grant_xp), group=2)
    app.add_handler(CommandHandler("rank", show_rank))
    app.add_handler(CommandHandler("top10", show_leaderboard))
