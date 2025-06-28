from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from googletrans import Translator

translator = Translator()

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("📘 Usage: /translate <text to translate>")

    text = " ".join(context.args)
    try:
        translated = translator.translate(text, dest='en')
        await update.message.reply_text(
            f"🗣️ Translated to English:\n\n{translated.text}"
        )
    except Exception as e:
        await update.message.reply_text("❌ Translation failed. Try again later.")
        print("Translation error:", e)

def register_translate_handler(app):
    app.add_handler(CommandHandler("translate", translate_command))
