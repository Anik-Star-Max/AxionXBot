# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import config
import handlers

application = Application.builder().token(config.BOT_TOKEN).build()

# 🔹 Command Handlers
application.add_handler(CommandHandler("start", handlers.start))
application.add_handler(CommandHandler("next", handlers.next_chat))
application.add_handler(CommandHandler("stop", handlers.stop_chat))
application.add_handler(CommandHandler("menu", handlers.menu))
application.add_handler(CommandHandler("settings", handlers.settings))
application.add_handler(CommandHandler("bonus", handlers.daily_bonus))
application.add_handler(CommandHandler("profile", handlers.profile))
application.add_handler(CommandHandler("rules", handlers.rules))
application.add_handler(CommandHandler("report", handlers.report_user))
application.add_handler(CommandHandler("language", handlers.set_language))
application.add_handler(CommandHandler("top_profiles", handlers.top_profiles))

# 🔹 Admin Handlers
application.add_handler(CommandHandler("ban", handlers.ban_user))
application.add_handler(CommandHandler("unban", handlers.unban_user))
application.add_handler(CommandHandler("vip", handlers.give_vip))
application.add_handler(CommandHandler("broadcast", handlers.broadcast))
application.add_handler(CommandHandler("stats", handlers.stats))
application.add_handler(CommandHandler("reports", handlers.reports))

# 🔹 Message & Callback
application.add_handler(CallbackQueryHandler(handlers.button_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text_input))

# 🔹 Start Bot
if __name__ == "__main__":
    print("🤖 AxionXBot started...")
    application.run_polling()
