from telegram.ext import ApplicationBuilder
import logging

# Init logging
logging.basicConfig(level=logging.INFO)

# Bot Token (replace this)
TOKEN = "YOUR_BOT_TOKEN"

# App
app = ApplicationBuilder().token(TOKEN).build()

# ====== Register Handlers ======
from handlers.otp import register_otp_handler
from handlers.referral import register_referral_handler
from handlers.xp import register_xp_handler
from handlers.ai_reply import register_ai_reply
from handlers.inbox import register_inbox_handler
from handlers.reminder import register_reminder_handler
from handlers.translate import register_translate_handler  # ✅ NEW

register_otp_handler(app)
register_referral_handler(app)
register_xp_handler(app)
register_ai_reply(app)
register_inbox_handler(app)
register_reminder_handler(app)
register_translate_handler(app)  # ✅ NEW

# ====== Start Scheduled Tasks ======
from utils.scheduler import start_daily_quote_task, start_reminder_task
start_daily_quote_task(app.bot)
start_reminder_task(app.bot)

# ====== Start App ======
if __name__ == "__main__":
    print("🤖 Bot is running...")
    app.run_polling()
