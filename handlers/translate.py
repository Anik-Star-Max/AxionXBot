from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from deep_translator import GoogleTranslator

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("📘 Usage: /translate <text to translate>")

    text = " ".join(context.args)
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        await update.message.reply_text(
            f"🗣️ Translated to English:\n\n{translated}"
        )
    except Exception as e:
        await update.message.reply_text("❌ Translation failed.")
        print("Translation error:", e)

def register_translate_handler(app):
    app.add_handler(CommandHandler("translate", translate_command))
