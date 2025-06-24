from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import config

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if uid not in users:
        users[uid] = {
            "banned": False,
            "diamonds": 0,
            "vip": False,
            "likes": 0,
            "translate": False
        }
        database.save("users", users)

    keyboard = [
        [InlineKeyboardButton("🎮 Start Chat", callback_data="start_chat")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to *AxionX Anonymous Chat Bot!*\n\nUse the menu below to navigate:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ---------------------------- BUTTON CALLBACK ----------------------------

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == "start_chat":
        await context.bot.send_message(uid, "🆕 Use /next to start chatting with a stranger.")

    elif query.data == "photo_roulette":
        await photo_roulette(update, context)

    elif query.data == "get_vip":
        await context.bot.send_message(uid, "💎 VIP packages:\n1 Day – 500 diamonds\n3 Days – 1500\n5 Days – 2500\n\nBuy via /getvip")

    elif query.data == "profile":
        await profile(update, context)

    elif query.data == "settings":
        await context.bot.send_message(uid, "⚙️ Coming soon: full profile & preferences editor.")

    elif query.data == "rules":
        await rules(update, context)

    elif query.data == "referral_top":
        await context.bot.send_message(uid, "🏆 Coming soon: Referral leaderboard!")
    elif query.data == "toggle_translate":
        users = database.load("users")
        current = users[str(uid)].get("translate", False)
        users[str(uid)]["translate"] = not current
        database.save("users", users)
        msg = "🈳 Translation is now ON." if not current else "❌ Translation is now OFF."
        await context.bot.send_message(uid, msg)

    elif query.data == "like_photo":
        users = database.load("users")
        uid = str(query.from_user.id)
        target_id = users[uid].get("current_photo_view")

        if target_id:
            users[target_id]["likes"] = users[target_id].get("likes", 0) + 1
            del users[uid]["current_photo_view"]
            database.save("users", users)
            await context.bot.send_message(uid, "❤️ You liked this profile!")

        await photo_roulette(update, context)

    elif query.data == "skip_photo":
        users = database.load("users")
        uid = str(query.from_user.id)
        users[uid].pop("current_photo_view", None)
        database.save("users", users)
        await context.bot.send_message(uid, "➡️ Skipped.")
        await photo_roulette(update, context)
# ---------------------------- GET VIP ----------------------------

async def get_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users = database.load("users")

    try:
        days = int(context.args[0])
        cost = days * 500
        user = users[str(uid)]

        if user.get("diamonds", 0) < cost:
            return await update.message.reply_text("💎 Not enough diamonds.")

        user["diamonds"] -= cost
        user["vip"] = True
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        user["vip_expiry"] = expiry.strftime("%Y-%m-%d")
        database.save("users", users)

        await update.message.reply_text(f"👑 VIP activated for {days} days!")
    except:
        await update.message.reply_text("❌ Usage: /getvip 1 | 3 | 5")
# ---------------------------- SET PROFILE PHOTO ----------------------------

async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if not update.message.photo:
        return await update.message.reply_text("📷 Please send a photo.")

    file_id = update.message.photo[-1].file_id
    users[uid]["profile_photo"] = file_id
    database.save("users", users)

    await update.message.reply_text("✅ Your anonymous profile photo has been set.")

# ---------------------------- PHOTO ROULETTE ----------------------------

async def photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    photo_users = [k for k, v in users.items() if v.get("profile_photo") and k != uid]
    if not photo_users:
        return await update.message.reply_text("🔄 No photos available yet.")

    choice = random.choice(photo_users)
    file_id = users[choice]["profile_photo"]

    users[uid]["current_photo_view"] = choice
    database.save("users", users)

    buttons = [
        [
            InlineKeyboardButton("❤️ Like", callback_data="like_photo"),
            InlineKeyboardButton("❌ Skip", callback_data="skip_photo")
        ]
    ]
    markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_photo(chat_id=uid, photo=file_id, caption="🔍 Stranger Profile", reply_markup=markup)
# ---------------------------- REFERRAL SYSTEM ----------------------------

async def referral_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")
    code = f"ref_{uid}"
    link = f"https://t.me/{config.BOT_USERNAME}?start={code}"
    count = users[uid].get("referrals", 0)

    await update.message.reply_text(
        f"🔗 Your referral link:\n{link}\n\n👥 Referrals: {count}\n\n🎁 Invite and earn 100 💎!"
    )

# To be added inside /start logic (ref check)
async def check_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].startswith("ref_"):
        ref_code = args[0].split("_")[1]
        referrer_id = str(ref_code)
        uid = str(update.effective_user.id)
        if referrer_id != uid:
            users = database.load("users")
            if "ref_by" not in users[uid]:
                users[uid]["ref_by"] = referrer_id
                users[referrer_id]["referrals"] = users[referrer_id].get("referrals", 0) + 1
                users[referrer_id]["diamonds"] = users[referrer_id].get("diamonds", 0) + 100
                users[uid]["diamonds"] = users[uid].get("diamonds", 0) + 50
                database.save("users", users)
                await update.message.reply_text("🎉 Referral successful! You earned 50 💎.")
# ---------------------------- START / NEXT / STOP CHAT ----------------------------

active_pairs = {}  # uid: partner_id
waiting_users = []

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await check_referral(update, context)  # apply referral if present

    if uid in active_pairs:
        return await update.message.reply_text("✅ You’re already in a chat. Use /stop to end it.")
    if uid in waiting_users:
        return await update.message.reply_text("⏳ Searching... Please wait.")

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_pairs[uid] = partner_id
        active_pairs[partner_id] = uid

        await context.bot.send_message(uid, "🔗 Connected! Say hi 👋")
        await context.bot.send_message(partner_id, "🔗 Connected! Say hi 👋")
    else:
        waiting_users.append(uid)
        await update.message.reply_text("⏳ Searching for a stranger... Please wait.")

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    partner_id = active_pairs.pop(uid, None)

    if uid in waiting_users:
        waiting_users.remove(uid)
        return await update.message.reply_text("❌ Search cancelled.")

    if partner_id:
        active_pairs.pop(partner_id, None)
        await context.bot.send_message(partner_id, "🚫 The other person left the chat.")
        await context.bot.send_message(uid, "🚫 You left the chat.")
    else:
        await update.message.reply_text("❌ You’re not in a chat.")

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_chat(update, context)
    await start_chat(update, context)
# ---------------------------- MESSAGE FORWARDING ----------------------------

from deep_translator import GoogleTranslator

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    partner_id = active_pairs.get(uid)

    if not partner_id:
        return await update.message.reply_text("❗ You're not in a chat. Use /next to find someone.")

    users = database.load("users")
    from_user = users.get(str(uid), {})
    to_user = users.get(str(partner_id), {})

    msg = update.message

    # Check if VIP translation is ON
    translate = from_user.get("vip") and from_user.get("translate", False)
    translated_text = None

    if translate and to_user.get("language") and to_user.get("language") != from_user.get("language"):
        try:
            translated_text = GoogleTranslator(
                source=from_user.get("language", "auto"),
                target=to_user["language"]
            ).translate(msg.text)
        except:
            translated_text = None

    try:
        if msg.text:
            await context.bot.send_message(
                chat_id=partner_id,
                text=translated_text if translated_text else msg.text
            )
        elif msg.sticker:
            await context.bot.send_sticker(chat_id=partner_id, sticker=msg.sticker.file_id)
        elif msg.photo:
            await context.bot.send_photo(chat_id=partner_id, photo=msg.photo[-1].file_id)
        elif msg.document:
            await context.bot.send_document(chat_id=partner_id, document=msg.document.file_id)
        elif msg.video:
            await context.bot.send_video(chat_id=partner_id, video=msg.video.file_id)
        else:
            await context.bot.send_message(chat_id=uid, text="⚠️ Unsupported message type.")
    except Exception as e:
        print("Message Forward Error:", e)
# ---------------------------- UI & MENU COMMANDS ----------------------------

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("🎲 Photo Roulette", callback_data="photo_roulette")],
        [InlineKeyboardButton("💎 Get VIP", callback_data="get_vip")],
        [InlineKeyboardButton("🏆 Referral TOP", callback_data="referral_top")],
        [InlineKeyboardButton("🈳 Translate Toggle", callback_data="toggle_translate")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔑 Menu:", reply_markup=reply_markup)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("rules.txt", "r") as f:
            content = f.read()
    except:
        content = "📜 Be kind, stay anonymous, and respect others.\n🚫 No spamming, harassment, or sharing personal info."
    await update.message.reply_text(content)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")
    user = users.get(uid, {})

    text = f"👤 Your Profile:\n\n"
    text += f"Gender: {user.get('gender', 'Not set')}\n"
    text += f"Age: {user.get('age', 'Not set')}\n"
    text += f"Language: {user.get('language', 'Not set')}\n"
    text += f"VIP: {'✅ Yes' if user.get('vip') else '❌ No'}\n"
    text += f"Diamonds: 💎 {user.get('diamonds', 0)}"

    await update.message.reply_text(text)

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")
    now = datetime.datetime.now().date()
    last_bonus = users[uid].get("last_bonus")

    if last_bonus == str(now):
        return await update.message.reply_text("⏳ You already claimed your daily bonus today!")

    users[uid]["last_bonus"] = str(now)
    users[uid]["diamonds"] = users[uid].get("diamonds", 0) + 100
    database.save("users", users)
    await update.message.reply_text("🎁 You received 100 💎 daily bonus!")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Profile editing coming soon...\nCurrently only available for VIPs.")
# ---------------------------- ADMIN + REPORT SYSTEM ----------------------------

ADMIN_ID = int(config.ADMIN_ID)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    partner_id = active_pairs.get(int(uid))

    if not partner_id:
        return await update.message.reply_text("⚠️ You must be in a chat to report someone.")

    reason = " ".join(context.args)
    if not reason:
        return await update.message.reply_text("❗ Please provide a reason: /report [reason]")

    complaint = f"🚨 Report by {uid} on {partner_id}\nReason: {reason}"
    users = database.load("users")

    # Save to complaints.json
    complaints = database.load("complaints")
    complaints[str(uid)] = {
        "against": str(partner_id),
        "reason": reason,
        "timestamp": str(datetime.datetime.now())
    }
    database.save("complaints", complaints)

    await update.message.reply_text("✅ Your report has been submitted.")
    await context.bot.send_message(ADMIN_ID, complaint)

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    uid = context.args[0]
    users = database.load("users")
    if uid in users:
        users[uid]["banned"] = True
        database.save("users", users)
        await update.message.reply_text(f"✅ User {uid} has been banned.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    uid = context.args[0]
    users = database.load("users")
    if uid in users:
        users[uid].pop("banned", None)
        database.save("users", users)
        await update.message.reply_text(f"✅ User {uid} has been unbanned.")

async def give_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = context.args[0]
        amount = int(context.args[1])
        users = database.load("users")
        users[uid]["diamonds"] = users[uid].get("diamonds", 0) + amount
        database.save("users", users)
        await update.message.reply_text(f"✅ {amount} 💎 given to {uid}.")
    except:
        await update.message.reply_text("❌ Usage: /give [user_id] [amount]")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    users = database.load("users")
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip"))
    banned = sum(1 for u in users.values() if u.get("banned"))
    await update.message.reply_text(f"📊 Stats:\nUsers: {total}\nVIPs: {vip}\nBanned: {banned}")

async def assign_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = context.args[0]
        days = int(context.args[1])
        users = database.load("users")
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        users[uid]["vip"] = True
        users[uid]["vip_expiry"] = expiry.strftime("%Y-%m-%d")
        database.save("users", users)
        await update.message.reply_text(f"✅ VIP given to {uid} for {days} days.")
    except:
        await update.message.reply_text("❌ Usage: /vip [user_id] [days]")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❌ Usage: /broadcast [message]")

    users = database.load("users")
    for uid in users:
        try:
            await context.bot.send_message(int(uid), msg)
        except:
            continue
    await update.message.reply_text("📢 Broadcast sent.")
# ---------------------------- SETUP HANDLERS ----------------------------

def setup_handlers(application):
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("bonus", daily_bonus))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("referral", referral_code))
    application.add_handler(CommandHandler("getvip", get_vip))
    application.add_handler(CommandHandler("photo", set_photo))
    application.add_handler(CommandHandler("photo_roulette", photo_roulette))
    application.add_handler(CommandHandler("report", report))

    # Admin-only
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("vip", assign_vip))
    application.add_handler(CommandHandler("give", give_diamonds))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))

    # Callback buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Chat messages
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    application.add_handler(MessageHandler(filters.PHOTO & (~filters.COMMAND), photo_handler))
