from apscheduler.schedulers.background import BackgroundScheduler
import random
import asyncio
from database import users, save_users

scheduler = BackgroundScheduler()
scheduler.start()

sad_quotes = [
    "🌑 It's hard to forget someone who gave you so much to remember.",
    "💔 Sometimes, you have to stay silent because no words can explain the pain.",
    "🕯 The worst kind of sad is not being able to explain why.",
    "📖 POV: You were healing but someone touched the wound again."
]

async def send_daily_quotes(bot):
    for uid in users:
        if users[uid].get("daily_quote", True):
            try:
                quote = random.choice(sad_quotes)
                await bot.send_message(chat_id=int(uid), text=quote)
            except:
                continue

def start_daily_quote_task(bot):
    loop = asyncio.get_event_loop()
    scheduler.add_job(lambda: loop.create_task(send_daily_quotes(bot)), 'interval', hours=6)

# =================== Reminders ====================

async def send_reminders(bot):
    to_remove = []
    for uid, data in users.items():
        for r in data.get("reminders", []):
            if r["time"] <= time.time():
                try:
                    await bot.send_message(chat_id=int(uid), text=f"⏰ Reminder: {r['text']}")
                except:
                    pass
                to_remove.append((uid, r))

    for uid, r in to_remove:
        users[uid]["reminders"].remove(r)
    save_users(users)

def start_reminder_task(bot):
    loop = asyncio.get_event_loop()
    scheduler.add_job(lambda: loop.create_task(send_reminders(bot)), 'interval', minutes=1)
