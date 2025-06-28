from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import users, save_users

# XP per referral (optional)
REFERRAL_XP = 10

# Share referral link
async def send_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"
    
    await update.message.reply_text(
        f"📲 *Your Referral Link:*\n\n{link}\n\n"
        f"Invite your friends and earn rewards!",
        parse_mode="Markdown"
    )

# Detect referral on /start
async def detect_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "first_name": user.first_name,
            "username": user.username or "",
            "referrer_id": None,
            "referrals": [],
            "xp": 0
        }

    if context.args:
        referrer_id = context.args[0]
        if referrer_id == user_id:
            return  # User can't refer themselves

        if not users[user_id].get("referrer_id"):
            if referrer_id in users:
                users[user_id]["referrer_id"] = referrer_id
                users[referrer_id].setdefault("referrals", []).append(user_id)
                users[referrer_id]["xp"] = users[referrer_id].get("xp", 0) + REFERRAL_XP

    save_users(users)

# Show referral list
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    referred_ids = users.get(user_id, {}).get("referrals", [])

    if not referred_ids:
        return await update.message.reply_text("👥 You haven't referred anyone yet.")

    lines = []
    for uid in referred_ids:
        u = users.get(uid, {})
        name = u.get("first_name", "Unknown")
        username = f"@{u['username']}" if u.get("username") else uid
        lines.append(f"• {name} ({username})")

    await update.message.reply_text(
        f"👥 *Your Referrals:*\n\n" + "\n".join(lines),
        parse_mode="Markdown"
    )

# Register referral handlers
def register_referral_handler(app):
    app.add_handler(CommandHandler("refer", send_referral))
    app.add_handler(CommandHandler("myreferrals", my_referrals))
    app.add_handler(CommandHandler("start", detect_referral))  # override
