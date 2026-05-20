import asyncio
import logging
from rubpy import BotClient
import config
from core import db
from modules.mute import mute_timer_worker
from modules.cleaner import reset_24_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scheduled_broadcast_task(bot):
    """Background task to send scheduled messages"""
    while True:
        try:
            messages = await db.get_scheduled_messages()
            for msg in messages:
                groups = await db.get_all_groups()
                for group in groups:
                    try:
                        await bot.forward_message(
                            config.ADMIN_GUIDS[0],  # از ادمین اول فوروارد می‌کنه
                            msg['message_id'],
                            group['group_guid']
                        )
                        await asyncio.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        print(f"Error forwarding to {group['group_guid']}: {e}")
                
                await db.update_scheduled_message_sent(msg['message_id'])
            
        except Exception as e:
            print(f"Scheduled broadcast error: {e}")
        
        await asyncio.sleep(300)  # Check every 5 minutes


async def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found!")
        return
    
    bot = BotClient(config.BOT_TOKEN, rate_limit=0.1, use_webhook=True)
    
    from handlers import register_handlers
    register_handlers(bot)

    logger.info("Database is running...")
    await db.connect()
    
    asyncio.create_task(mute_timer_worker(db))
    asyncio.create_task(reset_24_messages(db))
    asyncio.create_task(scheduled_broadcast_task(bot))

    logger.info("Bot is running...")
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
