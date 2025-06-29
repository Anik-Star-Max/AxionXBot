from telegram.ext import ApplicationBuilder
import logging
import os
import asyncio

# Init logging
logging.basicConfig(level=logging.INFO)

# Secure token
TOKEN = os.environ.get("BOT_TOKEN")

# Build app
app = ApplicationBuilder().token(TOKEN).build()

# ====== Register Handlers ======
from handlers.chat import (
    register_chat_handlers  # ✅ All SMC-style chat-related commands
)

register_chat_handlers(app)  # 📌 Register all chat-related commands

# ====== Start Scheduled Tasks (if needed) ======
# from utils.scheduler import start_daily_quote_task, start_reminder_task
# start_daily_quote_task(app.bot)
# start_reminder_task(app.bot)

# ====== Delete Webhook Before Polling ======
async def delete_old_webhook():
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Old webhook deleted.")
    except Exception as e:
        print(f"⚠️ Webhook delete error: {e}")

# ====== Start Bot ======
if __name__ == "__main__":
    print("🤖 Bot is running...")
    asyncio.run(delete_old_webhook())
    app.run_polling()
