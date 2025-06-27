# handlers.py (Part 1)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters)
import config
import database
import datetime
import random


# Active chats dictionary
active_chats = {}

# ➤ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if uid not in users:
        users[uid] = {"diamonds": 100, "joined": str(datetime.datetime.now())}
        database.save("users", users)
        await update.message.reply_text("🎉 Welcome to AxionX! You've received 100 💎 to start chatting!")
    else:
        await update.message.reply_text("👋 Welcome back! Use /next to find a stranger.")

    args = context.args
    if args and args[0].startswith("ref_"):
        ref_code = args[0].split("_")[1]
        if ref_code != uid:
            if "ref_by" not in users[uid]:
                users[uid]["ref_by"] = ref_code
                users[ref_code]["referrals"] = users[ref_code].get("referrals", 0) + 1
                users[ref_code]["diamonds"] = users[ref_code].get("diamonds", 0) + 100
                users[uid]["diamonds"] = users[uid].get("diamonds", 0) + 50
                database.save("users", users)
                await update.message.reply_text("🎉 Referral successful! You earned 50 💎.")

# ➤ /next command
async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if uid in active_chats:
        return await update.message.reply_text("❗ You're already in a chat. Use /stop to leave it.")

    for other_id in users:
        if other_id != uid and other_id not in active_chats.values() and users[other_id].get("searching"):
            active_chats[uid] = other_id
            active_chats[other_id] = uid
            users[uid]["searching"] = False
            users[other_id]["searching"] = False
            database.save("users", users)

            await context.bot.send_message(uid, "🔗 Connected! Say hi to your stranger.")
            await context.bot.send_message(other_id, "🔗 Connected! Say hi to your stranger.")
            return

    users[uid]["searching"] = True
    database.save("users", users)
    await update.message.reply_text("🔍 Searching for a stranger to connect...")

# ➤ /stop command
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in active_chats:
        return await update.message.reply_text("❌ You're not in a chat.")

    partner_id = active_chats.pop(uid)
    active_chats.pop(partner_id, None)

    await context.bot.send_message(uid, "🛑 You left the chat.")
    await context.bot.send_message(partner_id, "🚫 Stranger has left the chat.")

# ---------------------------- DAILY BONUS ----------------------------

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    user = users.get(uid)
    if not user:
        return await update.message.reply_text("❌ User not found.")

    now = datetime.datetime.now().date()
    last = user.get("last_bonus")

    if last == str(now):
        return await update.message.reply_text("🕒 You already claimed today's bonus.")

    user["diamonds"] = user.get("diamonds", 0) + 100
    user["last_bonus"] = str(now)
    database.save("users", users)

    await update.message.reply_text("🎁 You got 100 daily diamonds!")

# ---------------------------- PROFILE ----------------------------

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    user = users.get(uid, {})
    photo = user.get("profile_photo")
    text = f"👤 Your Profile\n\n💎 Diamonds: {user.get('diamonds', 0)}\n👥 Referrals: {user.get('referrals', 0)}"

    if photo:
        await update.message.reply_photo(photo=photo, caption=text)
    else:
        await update.message.reply_text(text)

# ---------------------------- RULES ----------------------------

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 Rules:\n\n1. No spam.\n2. Respect everyone.\n3. No inappropriate content.\n4. Admins have final say.\n\n🚫 Violation may lead to ban."
    )

# ---------------------------- MENU ----------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("👤 Profile", callback_data="profile"),
            InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
        ],
        [
            InlineKeyboardButton("🈳 Translate", callback_data="toggle_translate"),
            InlineKeyboardButton("📜 Rules", callback_data="rules")
        ],
        [
            InlineKeyboardButton("🎲 Photo Roulette", callback_data="photo_roulette"),
            InlineKeyboardButton("💎 Get VIP", callback_data="get_vip")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Menu", reply_markup=reply_markup)
# ---------------------------- GET VIP ----------------------------

async def get_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    try:
        days = int(context.args[0])
        cost = days * 500
        user = users.get(uid, {})

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

# ---------------------------- LIKE / SKIP PHOTO ----------------------------

async def handle_photo_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    users = database.load("users")

    if query.data == "like_photo":
        target_id = users[uid].get("current_photo_view")
        if target_id:
            users[target_id]["likes"] = users[target_id].get("likes", 0) + 1
            del users[uid]["current_photo_view"]
            database.save("users", users)
            await context.bot.send_message(uid, "❤️ You liked this profile!")
        await photo_roulette(update, context)

    elif query.data == "skip_photo":
        users[uid].pop("current_photo_view", None)
        database.save("users", users)
        await context.bot.send_message(uid, "➡️ Skipped.")
        await photo_roulette(update, context)
# ---------------------------- BUTTON CALLBACK ----------------------------

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    await query.answer()

    users = database.load("users")
    uid_str = str(uid)

    if query.data == "start_chat":
        await context.bot.send_message(uid, "🆕 Use /next to start chatting with a stranger.")

    elif query.data == "photo_roulette":
        await photo_roulette(update, context)

    elif query.data == "get_vip":
        await context.bot.send_message(
            uid,
            "💎 VIP packages:\n1 Day – 500 diamonds\n3 Days – 1500\n5 Days – 2500\n\nBuy via /getvip"
        )

    elif query.data == "profile":
        await profile(update, context)

    elif query.data == "settings":
        await context.bot.send_message(uid, "⚙️ Coming soon: full profile & preferences editor.")

    elif query.data == "rules":
        await rules(update, context)

    elif query.data == "referral_top":
        await context.bot.send_message(uid, "🏆 Coming soon: Referral leaderboard!")

    elif query.data == "toggle_translate":
        current = users[uid_str].get("translate", False)
        users[uid_str]["translate"] = not current
        database.save("users", users)
        msg = "🈳 Translation is now ON." if not current else "❌ Translation is now OFF."
        await context.bot.send_message(uid, msg)

    elif query.data in ["like_photo", "skip_photo"]:
        await handle_photo_buttons(update, context)
# ---------------------------- ADMIN COMMANDS ----------------------------

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    try:
        target = str(context.args[0])
        users = database.load("users")
        users[target]["banned"] = True
        database.save("users", users)
        await update.message.reply_text("✅ User banned.")
    except:
        await update.message.reply_text("❌ Usage: /ban <user_id>")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    try:
        target = str(context.args[0])
        users = database.load("users")
        users[target]["banned"] = False
        database.save("users", users)
        await update.message.reply_text("✅ User unbanned.")
    except:
        await update.message.reply_text("❌ Usage: /unban <user_id>")

async def assign_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    try:
        uid = str(context.args[0])
        days = int(context.args[1])
        users = database.load("users")
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        users[uid]["vip"] = True
        users[uid]["vip_expiry"] = expiry.strftime("%Y-%m-%d")
        database.save("users", users)
        await update.message.reply_text("✅ VIP assigned.")
    except:
        await update.message.reply_text("❌ Usage: /vip <user_id> <days>")

async def give_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    try:
        uid = str(context.args[0])
        amount = int(context.args[1])
        users = database.load("users")
        users[uid]["diamonds"] = users[uid].get("diamonds", 0) + amount
        database.save("users", users)
        await update.message.reply_text("✅ Diamonds sent.")
    except:
        await update.message.reply_text("❌ Usage: /give <user_id> <amount>")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    users = database.load("users")
    text = " ".join(context.args)
    count = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, text)
            count += 1
        except:
            continue
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
# ---------------------------- VIP PURCHASE ----------------------------

async def get_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    try:
        days = int(context.args[0])
        cost = days * 500
        user = users[uid]

        if user.get("diamonds", 0) < cost:
            return await update.message.reply_text("💎 Not enough diamonds.")

        # Deduct & activate
        user["diamonds"] -= cost
        user["vip"] = True
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        user["vip_expiry"] = expiry.strftime("%Y-%m-%d")
        database.save("users", users)

        await update.message.reply_text(f"👑 VIP activated for {days} days!")
    except:
        await update.message.reply_text("❌ Usage: /getvip 1 | 3 | 5")

# ---------------------------- PHOTO SYSTEM ----------------------------

async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if not update.message.photo:
        return await update.message.reply_text("📷 Please send a photo.")

    file_id = update.message.photo[-1].file_id
    users[uid]["profile_photo"] = file_id
    database.save("users", users)

    await update.message.reply_text("✅ Anonymous photo set!")

async def photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    photo_users = [k for k, v in users.items() if v.get("profile_photo") and k != uid]
    if not photo_users:
        return await update.message.reply_text("🔄 No photos available.")

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
        f"🔗 Your referral link:\n{link}\n\n👥 Referrals: {count}\n🎁 Invite and earn 100 💎!"
    )
# ---------------------------- /START COMMAND ----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if uid not in users:
        users[uid] = {
            "chatting": False,
            "banned": False,
            "vip": False,
            "diamonds": 100,
            "referrals": 0,
            "likes": 0,
        }
        database.save("users", users)

    # Referral logic
    args = context.args
    if args and args[0].startswith("ref_"):
        ref_code = args[0].split("_")[1]
        referrer_id = str(ref_code)
        if referrer_id != uid and "ref_by" not in users[uid]:
            users[uid]["ref_by"] = referrer_id
            users[referrer_id]["referrals"] = users[referrer_id].get("referrals", 0) + 1
            users[referrer_id]["diamonds"] = users[referrer_id].get("diamonds", 0) + 100
            users[uid]["diamonds"] = users[uid].get("diamonds", 0) + 50
            database.save("users", users)
            await update.message.reply_text("🎉 Referral successful! You earned 50 💎.")

    buttons = [
        [InlineKeyboardButton("🚀 Start Chatting", callback_data="start_chat")],
        [InlineKeyboardButton("🎲 Photo Roulette", callback_data="photo_roulette")],
        [InlineKeyboardButton("💎 Get VIP", callback_data="get_vip")],
        [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("🏆 Referrals", callback_data="referral_top")],
        [InlineKeyboardButton("🌐 Toggle Translate", callback_data="toggle_translate")],
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("👋 Welcome to AxionX ChatBot!\n\nChoose an option below 👇", reply_markup=markup)
    
    # ➤ /report command: Report current chat partner
async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    partner_id = active_chats.get(uid)

    if not partner_id:
        return await update.message.reply_text("❌ You're not in a chat to report someone.")

    # Load report database (if you maintain one)
    reports = database.load("reports")
    reports.append({"reporter": uid, "reported": partner_id, "time": str(datetime.datetime.now())})
    database.save("reports", reports)

    # Disconnect both users
    active_chats.pop(uid, None)
    active_chats.pop(partner_id, None)

    await context.bot.send_message(uid, "🚨 You've reported the stranger. Chat ended.")
    await context.bot.send_message(partner_id, "⚠️ You were reported by your stranger. Chat ended.")

# ➤ /language command
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇮🇳 Hindi", callback_data='lang_hi')],
        [InlineKeyboardButton("🌐 Bengali", callback_data='lang_bn')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌍 Choose your language:", reply_markup=reply_markup)

# ➤ Language callback handler
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)

    # Store selected language in database (if needed)
    users = database.load("users")
    if uid not in users:
        users[uid] = {}

    lang_code = query.data.replace("lang_", "")
    users[uid]["language"] = lang_code
    database.save("users", users)

    language_names = {"en": "English", "hi": "Hindi", "bn": "Bengali"}
    await query.edit_message_text(f"✅ Language set to: {language_names.get(lang_code, 'Unknown')}")

# ➤ /top_profiles command: Show users with most referrals
async def top_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = database.load("users")
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("referrals", 0), reverse=True)[:5]

    if not sorted_users:
        await update.message.reply_text("📉 No referral data found.")
        return

    msg = "🏆 *Top 5 Profiles by Referrals:*\n\n"
    for idx, (uid, data) in enumerate(sorted_users, start=1):
        username = f"[User](tg://user?id={uid})"
        referrals = data.get("referrals", 0)
        msg += f"{idx}. {username} - {referrals} referrals\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# ---------------------------- BUTTON CALLBACK CONTINUED ----------------------------

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == "start_chat":
        await context.bot.send_message(uid, "🆕 Use /next to find a stranger.")

    elif query.data == "photo_roulette":
        await photo_roulette(update, context)

    elif query.data == "get_vip":
        await context.bot.send_message(uid, "💎 VIP: 1 Day - 500 💎\n3 Days - 1500\n5 Days - 2500\nBuy using /getvip")

    elif query.data == "profile":
        await profile(update, context)

    elif query.data == "settings":
        await context.bot.send_message(uid, "⚙️ Coming soon: Edit profile & preferences.")

    elif query.data == "rules":
        await rules(update, context)

    elif query.data == "referral_top":
        await context.bot.send_message(uid, "🏆 Leaderboard coming soon!")

    elif query.data == "toggle_translate":
        users = database.load("users")
        current = users[str(uid)].get("translate", False)
        users[str(uid)]["translate"] = not current
        database.save("users", users)
        msg = "🌐 Translation ON." if not current else "❌ Translation OFF."
        await context.bot.send_message(uid, msg)

    elif query.data == "like_photo":
        users = database.load("users")
        target_id = users[str(uid)].get("current_photo_view")
        if target_id:
            users[target_id]["likes"] = users[target_id].get("likes", 0) + 1
            del users[str(uid)]["current_photo_view"]
            database.save("users", users)
            await context.bot.send_message(uid, "❤️ You liked the profile!")
        await photo_roulette(update, context)

    elif query.data == "skip_photo":
        users = database.load("users")
        users[str(uid)].pop("current_photo_view", None)
        database.save("users", users)
        await context.bot.send_message(uid, "➡️ Skipped.")
        await photo_roulette(update, context)
# ---------------------------- TEXT MESSAGE HANDLER ----------------------------

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if users[uid].get("banned"):
        return await update.message.reply_text("🚫 You are banned.")

    if not users[uid].get("chatting"):
        return await update.message.reply_text("❗ You're not chatting with anyone.\nUse /next to find a stranger.")

    partner_id = users[uid].get("partner")
    if not partner_id:
        return await update.message.reply_text("⚠️ Partner not found. Use /stop and then /next.")

    text = update.message.text

    # Translate if needed
    if users[partner_id].get("translate"):
        from deep_translator import GoogleTranslator
        try:
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            text += f"\n\n🌐 Translated:\n_{translated}_"
        except:
            pass

    await context.bot.send_message(chat_id=partner_id, text=text)

# ---------------------------- PHOTO HANDLER ----------------------------

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if users[uid].get("banned"):
        return await update.message.reply_text("🚫 You are banned.")

    if not users[uid].get("chatting"):
        return await update.message.reply_text("❗ You're not chatting with anyone.\nUse /next to find a stranger.")

    partner_id = users[uid].get("partner")
    if not partner_id:
        return await update.message.reply_text("⚠️ Partner not found. Use /stop and then /next.")

    file_id = update.message.photo[-1].file_id
    await context.bot.send_photo(chat_id=partner_id, photo=file_id)

# ---------------------------- SETUP HANDLERS ----------------------------

def setup_handlers(application):
    # User Commands
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
    application.add_handler(CommandHandler("report", report_user))
    application.add_handler(CommandHandler("language", set_language))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CommandHandler("top_profiles", top_profiles))

    # Admin Commands
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("vip", give_vip))
    application.add_handler(CommandHandler("give", give_diamonds))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("reports", reports))

    # Buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, photo_handler))
