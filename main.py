from telegram.ext import Application
from handlers import setup_handlers
import config
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    setup_handlers(application)
    print("🤖 AxionXBot started...")
    application.run_polling()

if __name__ == "__main__":
    main()

