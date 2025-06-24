# handlers_premium.py – Part 1 (Gender & Age Match Filters)

from telegram import ReplyKeyboardMarkup

# Set gender command
async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users = database.load("users")
    gender = context.args[0].lower() if context.args else None

    if gender not in ["male", "female", "other"]:
        return await update.message.reply_text("❌ Usage: /gender male/female/other")

    users[str(uid)]["gender"] = gender
    database.save("users", users)
    await update.message.reply_text(f"✅ Gender set to {gender.capitalize()}.")

# Set age command
async def set_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users = database.load("users")

    try:
        age = int(context.args[0])
        if age < 10 or age > 100:
            return await update.message.reply_text("❌ Age must be between 10 and 100.")
    except:
        return await update.message.reply_text("❌ Usage: /age 18")

    users[str(uid)]["age"] = age
    database.save("users", users)
    await update.message.reply_text(f"✅ Age set to {age}.")

# Match filters inside /next (modifies existing function)
def match_filters(user1, user2):
    # Admins bypass filter
    if user1["vip"] or user1["id"] == config.ADMIN_ID:
        return True
    if user2["vip"] or user2["id"] == config.ADMIN_ID:
        return True

    # Gender match logic
    if "match_gender" in user1 and user1["match_gender"] != user2.get("gender"):
        return False
    if "match_gender" in user2 and user2["match_gender"] != user1.get("gender"):
        return False

    # Age match logic
    if "match_age_min" in user1 and user2.get("age", 0) < user1["match_age_min"]:
        return False
    if "match_age_max" in user1 and user2.get("age", 200) > user1["match_age_max"]:
        return False

    return True

# Set match filters (for VIPs)
async def set_match_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users = database.load("users")
    if not users[str(uid)]["vip"]:
        return await update.message.reply_text("💎 VIP only feature.")

    gender = context.args[0].lower() if context.args else None
    if gender not in ["male", "female", "other"]:
        return await update.message.reply_text("❌ Usage: /matchgender male/female/other")

    users[str(uid)]["match_gender"] = gender
    database.save("users", users)
    await update.message.reply_text(f"🎯 Match preference set to {gender.capitalize()}.")

async def set_match_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users = database.load("users")

    if not users[str(uid)]["vip"]:
        return await update.message.reply_text("💎 VIP only feature.")

    try:
        min_age = int(context.args[0])
        max_age = int(context.args[1])
        if min_age < 10 or max_age > 100 or min_age > max_age:
            return await update.message.reply_text("❌ Valid age range is 10 to 100.")
    except:
        return await update.message.reply_text("❌ Usage: /matchage 18 30")

    users[str(uid)]["match_age_min"] = min_age
    users[str(uid)]["match_age_max"] = max_age
    database.save("users", users)

    await update.message.reply_text(f"🎯 Match age set: {min_age} - {max_age}")
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# /menu with inline buttons
async def inline_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("💬 Start Chat", callback_data="start_chat")],
        [InlineKeyboardButton("🎲 Photo Roulette", callback_data="photo_roulette")],
        [InlineKeyboardButton("🎁 Get VIP", callback_data="get_vip")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("🧠 Settings", callback_data="settings")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("🏆 Referral TOP", callback_data="referral_top")],
        [InlineKeyboardButton("🌐 Translate Toggle", callback_data="toggle_translate")]
    ]

    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("🔘 Choose an option:", reply_markup=markup)
# CallbackQueryHandler function
import datetime
import random

# 👇 This function will handle all inline button callbacks
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()  # prevent loading spinner
    users = database.load("users")

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
        current = users[str(uid)].get("translate", False)
        users[str(uid)]["translate"] = not current
        database.save("users", users)
        msg = "🈳 Translation is now ON." if not current else "❌ Translation is now OFF."
        await context.bot.send_message(uid, msg)

    elif query.data == "like_photo":
        target_id = users[str(uid)].get("current_photo_view")
        if target_id:
            users[target_id]["likes"] = users[target_id].get("likes", 0) + 1
            del users[str(uid)]["current_photo_view"]
            database.save("users", users)
            await context.bot.send_message(uid, "❤️ You liked this profile!")
        await photo_roulette(update, context)

    elif query.data == "skip_photo":
        users[str(uid)].pop("current_photo_view", None)
        database.save("users", users)
        await context.bot.send_message(uid, "➡️ Skipped.")
        await photo_roulette(update, context)

# 👇 /getvip <days>
async def get_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    try:
        days = int(context.args[0])
        cost = days * 500
        user = users[uid]

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

# 👇 /photo - save profile pic
async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    if not update.message.photo:
        return await update.message.reply_text("📷 Please send a photo.")

    file_id = update.message.photo[-1].file_id
    users[uid]["profile_photo"] = file_id
    database.save("users", users)

    await update.message.reply_text("✅ Your anonymous profile photo has been set.")

# 👇 /photo_roulette - show random stranger profile
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

    buttons = [[
        InlineKeyboardButton("❤️ Like", callback_data="like_photo"),
        InlineKeyboardButton("❌ Skip", callback_data="skip_photo")
    ]]
    markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_photo(chat_id=uid, photo=file_id, caption="🔍 Stranger Profile", reply_markup=markup)

# In your start function, add this logic:

    args = context.args
    if args and args[0].startswith("ref_"):
        ref_code = args[0].split("_")[1]
        referrer_id = str(ref_code)
        uid = str(update.effective_user.id)
        if referrer_id != uid:
            users = database.load("users")
            if "ref_by" not in users[uid]:  # avoid duplicate
                users[uid]["ref_by"] = referrer_id
                users[referrer_id]["referrals"] = users[referrer_id].get("referrals", 0) + 1
                users[referrer_id]["diamonds"] = users[referrer_id].get("diamonds", 0) + 100
                users[uid]["diamonds"] = users[uid].get("diamonds", 0) + 50
                database.save("users", users)
                await update.message.reply_text("🎉 Referral successful! You earned 50 💎.")
# /referral – show personal referral code
async def referral_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")
    code = f"ref_{uid}"
    link = f"https://t.me/{config.BOT_USERNAME}?start={code}"
    count = users[uid].get("referrals", 0)

    await update.message.reply_text(
        f"🔗 Your referral link:\n{link}\n\n👥 Referrals: {count}\n\n🎁 Invite and earn 100 💎!"
    )
# /referral_top – top users by referrals
async def referral_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = database.load("users")

    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1].get("referrals", 0),
        reverse=True
    )

    msg = "🏆 Top Referrers:\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10]):
        visible = data.get("show_referral", True)
        name = data.get("name", f"User {uid}") if visible else "🔒 Hidden"
        count = data.get("referrals", 0)
        msg += f"{i+1}. {name} — {count} referrals\n"

    await update.message.reply_text(msg)
# translation.py

from deep_translator import GoogleTranslator

def translate(text, source, target):
    try:
        if source == target:
            return text
        return GoogleTranslator(source=source, target=target).translate(text)
    except Exception as e:
        print("Translation error:", e)
        return text
# /language en
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    try:
        lang = context.args[0]
        users[uid]["language"] = lang
        database.save("users", users)
        await update.message.reply_text(f"🌐 Your language is set to: {lang}")
    except:
        await update.message.reply_text("❌ Usage: /language en\nTry ISO codes like en, hi, es, etc.")
    elif query.data == "toggle_translate":
        uid = str(query.from_user.id)
        users = database.load("users")

        if not users[uid].get("vip"):
            return await context.bot.send_message(uid, "💎 VIP only feature.")

        current = users[uid].get("translate", False)
        users[uid]["translate"] = not current
        database.save("users", users)

        msg = "🈳 Translation is now ON." if not current else "❌ Translation is now OFF."
        await context.bot.send_message(uid, msg)
from translation import translate

async def forward_message(context, sender_id, message):
    users = database.load("users")
    partner_id = users[sender_id].get("partner")

    if not partner_id or str(partner_id) not in users:
        return

    sender_lang = users[sender_id].get("language", "en")
    receiver_lang = users[partner_id].get("language", "en")

    should_translate = users[partner_id].get("translate", False)

    text = message.text
    if should_translate and text:
        text = translate(text, source=sender_lang, target=receiver_lang)

    await context.bot.send_message(chat_id=partner_id, text=text)
# /ban <user_id>
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return

    try:
        uid = context.args[0]
        users = database.load("users")
        users[uid]["banned"] = True
        database.save("users", users)
        await update.message.reply_text(f"🔨 User {uid} has been banned.")
    except:
        await update.message.reply_text("❌ Usage: /ban <user_id>")

# /unban <user_id>
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return

    try:
        uid = context.args[0]
        users = database.load("users")
        users[uid]["banned"] = False
        database.save("users", users)
        await update.message.reply_text(f"✅ User {uid} has been unbanned.")
    except:
        await update.message.reply_text("❌ Usage: /unban <user_id>")

# /vip <user_id> <days>
async def give_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return

    try:
        uid = context.args[0]
        days = int(context.args[1])
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)

        users = database.load("users")
        users[uid]["vip"] = True
        users[uid]["vip_expiry"] = expiry.strftime("%Y-%m-%d")
        database.save("users", users)

        await update.message.reply_text(f"👑 Given VIP to {uid} for {days} days.")
    except:
        await update.message.reply_text("❌ Usage: /vip <user_id> <days>")
# /broadcast <message>
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return

    text = " ".join(context.args)
    users = database.load("users")
    count = 0

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            count += 1
        except:
            continue

    await update.message.reply_text(f"📢 Broadcast sent to {count} users.")
# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return

    users = database.load("users")
    total = len(users)
    banned = len([u for u in users.values() if u.get("banned")])
    vip = len([u for u in users.values() if u.get("vip")])
    photos = len([u for u in users.values() if u.get("profile_photo")])
    referrals = sum([u.get("referrals", 0) for u in users.values()])

    await update.message.reply_text(
        f"📊 Stats:\n\n👤 Users: {total}\n⛔ Banned: {banned}\n👑 VIPs: {vip}\n📷 Photos: {photos}\n🔗 Total Referrals: {referrals}"
    )
# /reports
async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return

    complaints = database.load("complaints")
    if not complaints:
        return await update.message.reply_text("🚨 No reports yet.")

    msg = "🛑 Reports:\n\n"
    for r in complaints.values():
        msg += f"From: {r['from']}\nAgainst: {r['against']}\nText: {r['text']}\n---\n"

    await update.message.reply_text(msg[:4096])  # Limit by Telegram max msg
# /bonus – daily diamonds 💎
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    now = datetime.datetime.now()
    user = users.get(uid, {})

    last_claim = user.get("last_bonus")
    if last_claim:
        last_time = datetime.datetime.strptime(last_claim, "%Y-%m-%d %H:%M:%S")
        delta = now - last_time
        if delta.total_seconds() < 86400:
            remaining = 86400 - delta.total_seconds()
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            return await update.message.reply_text(
                f"⏳ Come back in {hours}h {mins}m for your next bonus!"
            )

    # Give bonus
    vip = user.get("vip", False)
    bonus = 200 if vip else 100

    users[uid]["diamonds"] = users[uid].get("diamonds", 0) + bonus
    users[uid]["last_bonus"] = now.strftime("%Y-%m-%d %H:%M:%S")
    database.save("users", users)

    await update.message.reply_text(f"🎉 You earned {bonus} 💎 today! Come back tomorrow.")
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")
    user = users.get(uid, {})

    name = user.get("name", "No name")
    gender = user.get("gender", "Not set")
    lang = user.get("language", "en")
    visible = user.get("show_referral", True)
    vip = user.get("vip", False)

    msg = f"""⚙️ Your Settings:

👤 Name: {name}
🚻 Gender: {gender}
🌐 Language: {lang}
🔗 Show in Referral Top: {"✅ Yes" if visible else "❌ No"}
👑 VIP: {"Yes" if vip else "No"}
    """

    buttons = [
        [InlineKeyboardButton("✏️ Change Name", callback_data="set_name")],
        [InlineKeyboardButton("🚻 Change Gender", callback_data="set_gender")],
        [InlineKeyboardButton("🌐 Change Language", callback_data="set_lang")],
        [InlineKeyboardButton("🔗 Toggle Referral Top", callback_data="toggle_referral")],
    ]

    if vip:
        buttons.append([InlineKeyboardButton("👍👎 Set Like/Dislike Emoji", callback_data="set_emoji")])

    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(msg, reply_markup=markup)
    elif query.data == "toggle_referral":
        uid = str(query.from_user.id)
        users = database.load("users")
        current = users[uid].get("show_referral", True)
        users[uid]["show_referral"] = not current
        database.save("users", users)
        await query.answer("Toggled!")
        await context.bot.send_message(uid, f"🔗 Referral Top: {'✅ Shown' if not current else '❌ Hidden'}")

    elif query.data == "set_name":
        context.user_data["setting"] = "name"
        await context.bot.send_message(query.from_user.id, "👤 Send your new name.")

    elif query.data == "set_gender":
        context.user_data["setting"] = "gender"
        await context.bot.send_message(query.from_user.id, "🚻 Send your gender (Male/Female/Other).")

    elif query.data == "set_lang":
        context.user_data["setting"] = "language"
        await context.bot.send_message(query.from_user.id, "🌐 Send language code (e.g., en, hi).")

    elif query.data == "set_emoji":
        uid = str(query.from_user.id)
        users = database.load("users")
        if not users[uid].get("vip"):
            await query.answer("VIP only")
        else:
            context.user_data["setting"] = "emoji"
            await context.bot.send_message(uid, "👍 Send your like and dislike emoji separated by space.")
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = database.load("users")

    setting = context.user_data.get("setting")
    if not setting:
        return  # Not a setting input

    value = update.message.text.strip()

    if setting == "name":
        users[uid]["name"] = value
        await update.message.reply_text("✅ Name updated.")
    elif setting == "gender":
        users[uid]["gender"] = value
        await update.message.reply_text("✅ Gender updated.")
    elif setting == "language":
        users[uid]["language"] = value
        await update.message.reply_text("✅ Language updated.")
    elif setting == "emoji":
        parts = value.split()
        if len(parts) == 2:
            users[uid]["like_emoji"] = parts[0]
            users[uid]["dislike_emoji"] = parts[1]
            await update.message.reply_text("👍👎 Emojis updated.")
        else:
            await update.message.reply_text("❌ Send two emojis separated by space.")

    context.user_data["setting"] = None
    database.save("users", users)
# Ask for like/dislike after ending
await context.bot.send_message(uid, "🤔 How was your partner?\nSend 👍 or 👎 to give feedback.")
context.user_data["feedback"] = partner_id
    feedback_for = context.user_data.get("feedback")
    if feedback_for:
        emoji = update.message.text.strip()
        if emoji in ["👍", "👎"]:
            users = database.load("users")
            profile = users.get(str(feedback_for), {})
            if emoji == "👍":
                profile["likes"] = profile.get("likes", 0) + 1
            else:
                profile["dislikes"] = profile.get("dislikes", 0) + 1
            users[str(feedback_for)] = profile
            database.save("users", users)
            await update.message.reply_text("✅ Feedback submitted.")
        else:
            await update.message.reply_text("❌ Please send only 👍 or 👎")
        context.user_data["feedback"] = None
async def top_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = database.load("users")

    visible_users = {
        uid: data for uid, data in users.items()
        if data.get("show_top", True)
    }

    sorted_users = sorted(
        visible_users.items(),
        key=lambda x: x[1].get("likes", 0),
        reverse=True
    )

    msg = "🏆 Most Liked Profiles:\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10]):
        name = data.get("name", "Anonymous")
        likes = data.get("likes", 0)
        msg += f"{i+1}. {name} — 👍 {likes}\n"

    if msg == "🏆 Most Liked Profiles:\n\n":
        msg += "No liked profiles yet."

    await update.message.reply_text(msg)
[InlineKeyboardButton("🕵️ Hide/Show Top Profile", callback_data="toggle_top")],
elif query.data == "toggle_top":
    uid = str(query.from_user.id)
    users = database.load("users")
    current = users[uid].get("show_top", True)
    users[uid]["show_top"] = not current
    database.save("users", users)
    msg = "🕵️ Now your profile is hidden from Top." if not current else "✅ Your profile is visible in Top."
    await context.bot.send_message(uid, msg)
