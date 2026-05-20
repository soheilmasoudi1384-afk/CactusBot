import asyncio
import datetime

async def reset_24_messages(db):
    """
    تسک پس‌زمینه برای ریست پیام های 24 ساعت اخیر کاربران
    هر یک روز اجرا می‌شود.
    """
    executed_today = False
    while True:
        now = datetime.datetime.now()

        if now.hour == 0 and now.minute == 0 and not executed_today:
            await db.reset_daily_messages()
            executed_today = True

        if now.hour == 0 and now.minute == 1:
            executed_today = False

        await asyncio.sleep(10)
