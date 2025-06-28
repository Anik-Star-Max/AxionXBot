from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import users, save_users

ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# User sends message to admin
async def ask_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if len(context.args) == 0:
        return await update.message.reply_text("📝 Use: /ask <your message>")

    text = " ".join(context.args)
    message = f"📩 *New Inbox Message:*\n\n" \
              f"👤 From: [{user.first_name}](tg://user?id={user.id})\n" \
              f"🆔 UserID: `{user_id}`\n\n" \
              f"💬 Message:\n{text}"

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="Markdown")
        await update.message.reply_text("✅ Sent to admin. You’ll get a reply soon.")
    except:
        await update.message.reply_text("❌ Couldn't send message to admin.")

# Admin replies to forwarded message
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user inbox message to respond.")

    # Extract user ID from replied message (assumed inside markdown code block)
    lines = update.message.reply_to_message.text.splitlines()
    uid_line = next((line for line in lines if "UserID:" in line), None)
    if not uid_line:
        return await update.message.reply_text("❌ Couldn't extract user ID.")

    user_id = uid_line.split("`")[1]

    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"📬 *Admin replied:*\n\n{update.message.text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Replied to user.")
    except:
        await update.message.reply_text("❌ Failed to deliver your reply.")

# Register handlers
def register_inbox_handler(app):
    app.add_handler(CommandHandler("ask", ask_admin))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, reply_to_user))
