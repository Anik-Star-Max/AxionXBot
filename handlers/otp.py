import random
import time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database import users, save_users

OTP_VALIDITY_SECONDS = 180  # 3 minutes
otp_store = {}  # user_id: {"otp": ..., "expires": ...}

def generate_otp():
    return str(random.randint(100000, 999999))

async def start_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    otp = generate_otp()
    expires = time.time() + OTP_VALIDITY_SECONDS
    otp_store[user_id] = {"otp": otp, "expires": expires}

    # Send OTP privately
    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"🔐 *Your OTP Code:* `{otp}`\n\n_Valid for 3 minutes_\n\nSend it like: `/code {otp}`",
            parse_mode="Markdown"
        )
        await update.message.reply_text("📩 OTP sent to your DM. Check and submit it using /code")
    except:
        await update.message.reply_text("❌ Couldn't send OTP. Please start the bot privately.")

async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        return await update.message.reply_text("Usage: /code <OTP>")

    code = context.args[0]
    record = otp_store.get(user_id)

    if not record:
        return await update.message.reply_text("⚠️ No OTP found. Use /verify to generate one.")

    if time.time() > record["expires"]:
        del otp_store[user_id]
        return await update.message.reply_text("⏳ OTP expired. Use /verify again.")

    if code != record["otp"]:
        return await update.message.reply_text("❌ Incorrect OTP. Please try again.")

    # Mark user as verified
    users[user_id]["verified"] = True
    save_users(users)
    del otp_store[user_id]

    await update.message.reply_text("✅ OTP verified! Your account is now secure.")

# Utility to check if user is verified
def is_verified(user_id: str) -> bool:
    return users.get(user_id, {}).get("verified", False)

# Register in app
def register_otp_handler(app):
    app.add_handler(CommandHandler("verify", start_verification))
    app.add_handler(CommandHandler("code", verify_otp))
