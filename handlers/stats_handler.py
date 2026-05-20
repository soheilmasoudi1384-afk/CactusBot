from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update
from core import db
import jdatetime

def register_stats_handlers(bot: BotClient):

    async def check_admin(group_guid, user_guid):
        member = await db.get_group_member(group_guid, user_guid)
        if not member:
            return False
        return member["user_rank"] in ["admin", "owner"]

    @bot.on_update(filters.group)
    async def handle_stats(client: BotClient, message: Update):
        group_guid = message.chat_id
        if not message.new_message or not message.new_message.text:
            return
        
        msg_text = message.new_message.text.strip()
        user_guid = message.new_message.sender_id

        # گزارشات
        if msg_text in ["گزارشات", "آمار کامل"]:
            if not await check_admin(group_guid, user_guid):
                return
            
            reports = await db.get_group_reports(group_guid)
            total_messages = await db.get_group_total_messages(group_guid)
            
            text = "📊 **گزارشات کامل گروه**\n\n"
            text += f"📝 متن: {reports.get('text', 0)}\n"
            text += f"🔗 لینک: {reports.get('link', 0)}\n"
            text += f"🚫 فحش: {reports.get('profanity', 0)}\n"
            text += f"🎬 فیلم: {reports.get('video', 0)}\n"
            text += f"🆔 آیدی: {reports.get('id', 0)}\n"
            text += f"⛔ کلمات غیرمجاز: {reports.get('forbidden_words', 0)}\n"
            text += f"🎙️ ویس: {reports.get('voice', 0)}\n"
            text += f"📷 عکس: {reports.get('photo', 0)}\n"
            text += f"↪️ فوروارد: {reports.get('forward', 0)}\n"
            text += f"💥 کد هنگی: {reports.get('hang_code', 0)}\n"
            text += f"🎭 استیکر: {reports.get('sticker', 0)}\n"
            text += f"📊 نظرسنجی: {reports.get('poll', 0)}\n"
            text += f"🎨 متادیتا: {reports.get('metadata', 0)}\n"
            text += f"🎵 آهنگ: {reports.get('music', 0)}\n"
            text += f"📦 فایل: {reports.get('file', 0)}\n"
            text += f"🎬 گیف: {reports.get('gif', 0)}\n\n"
            text += f"**📈 کل پیام‌ها: {total_messages}**"
            
            await message.reply(text)
            return

        # گزارشات روزانه
        if msg_text in ["گزارشات روزانه", "آمار امروز"]:
            if not await check_admin(group_guid, user_guid):
                return
            
            today_messages = await db.get_group_total_messages_today(group_guid)
            top_members = await db.get_top3_active_members(group_guid)
            
            text = f"📈 **گزارشات روزانه - {jdatetime.date.today()}**\n\n"
            text += f"📝 کل پیام‌های امروز: {today_messages}\n\n"
            text += "👥 **اعضای فعال:**\n"
            
            for idx, member in enumerate(top_members, 1):
                if member["user_guid"] != "-":
                    user_name = await db.get_user_display_name(group_guid, member["user_guid"])
                    text += f"{idx}. [{user_name}]({member['user_guid']}) - {member['messages_today']} پیام\n"
                else:
                    text += f"{idx}. بدون داده\n"
            
            await message.reply(text)
            return

        # گزارشات هفتگی
        if msg_text in ["گزارشات هفتگی", "آمار هفته"]:
            if not await check_admin(group_guid, user_guid):
                return
            
            today = jdatetime.date.today()
            text = f"📊 **آمار هفتگی**\n\n"
            text += f"نام گروه: {(await client.get_chat(group_guid)).title}\n"
            text += f"تاریخ: {today}\n\n"
            
            top_members = await db.get_top_group_members(group_guid, limit=10)
            text += "👥 **کاربران برتر این هفته:**\n"
            
            for idx, member in enumerate(top_members, 1):
                user_name = await db.get_user_display_name(group_guid, member["user_guid"])
                text += f"{idx}. [{user_name}]({member['user_guid']}) - {member['message_count']} پیام\n"
            
            await message.reply(text)
            return

        # آمار کاربر (روی ریپلای)
        if msg_text in ["آمار کاربر", "امار کاربر"] and message.new_message.reply_to_message_id:
            # من در group_handler آن رو پیاده کردم
            pass
