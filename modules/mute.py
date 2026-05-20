import asyncio

async def mute_timer_worker(db):
    """
    تسک پس‌زمینه برای کاهش زمان سکوت کاربران
    هر ۶۰ ثانیه اجرا می‌شود.
    """
    while True:
        # صبر کردن به مدت ۱ دقیقه (۶۰ ثانیه)
        await asyncio.sleep(60) 
        
        # کم کردن یک واحد از زمان سکوت تمامی کاربرانی که میوت هستند
        await db.decrement_all_mutes()
        await db.decrement_all_muted_groups()
