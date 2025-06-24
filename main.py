# main.py
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import config, handlers

def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("next", handlers.next_chat))
    app.add_handler(CommandHandler("stop", handlers.stop_chat))
    app.add_handler(CommandHandler(["menu", "settings"], handlers.menu))
    app.add_handler(CommandHandler("bonus", handlers.daily_bonus))
    app.add_handler(CommandHandler("profile", handlers.profile))
    app.add_handler(CommandHandler("rules", handlers.rules))
    app.add_handler(CommandHandler("report", handlers.report))
    
    # Admin commands
    app.add_handler(CommandHandler("ban", handlers.ban_user))
    app.add_handler(CommandHandler("unban", handlers.unban_user))
    app.add_handler(CommandHandler("broadcast", handlers.broadcast))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("givevip", handlers.give_vip))
    app.add_handler(CommandHandler("givediamonds", handlers.give_diamonds))

    # Message forwarder (text, photo, sticker)
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.STICKER,
        handlers.forward_message
    ))

    # Error handler
    app.add_error_handler(handlers.error_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
