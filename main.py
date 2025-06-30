from telegram.ext import ApplicationBuilder
import logging
import os
import asyncio

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load the bot token from environment
TOKEN = os.environ.get("BOT_TOKEN")

# Build the bot application
app = ApplicationBuilder().token(TOKEN).build()

# ====== Register All Handlers ======
from handlers.chat import register_chat_handlers  # All command/message handlers

register_chat_handlers(app)  # Register handlers from chat.py

# ====== Delete Old Webhook Before Polling ======
async def delete_old_webhook():
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Old webhook deleted.")
    except Exception as e:
        print(f"⚠️ Webhook delete error: {e}")

# ====== Run the Bot ======
if __name__ == "__main__":
    print("🤖 Bot is running...")
    asyncio.run(delete_old_webhook())
    app.run_polling()
