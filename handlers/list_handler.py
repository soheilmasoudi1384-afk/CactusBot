from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update
from core import db
from utils.texts import load_texts, t
import json

def register_list_handlers(bot: BotClient):
    texts = load_texts("locales/texts.json")

    async def check_admin(group_guid, user_guid):
        member = await db.get_group_member(group_guid, user_guid)
        if not member:
            return False
        return member["user_rank"] in ["admin", "owner"]

    @bot.on_update(filters.group)
    async def handle_lists(client: BotClient, message: Update):
        group_guid = message.chat_id
        if not message.new_message or not message.new_message.text:
            return
        
        msg_text = message.new_message.text.strip()
        user_guid = message.new_message.sender_id

        # دستور اصلی لیست
        if msg_text == "لیست":
            if not await check_admin(group_guid, user_guid):
                await message.reply("❌ فقط ادمین و مالک می‌تونن استفاده کنند")
                return
            
            menu = """
**📋 منوی لیست‌ها**

🔹 **بخش مدیریت:**
• لیست پاکسازی
• لیست ریست
  ├─ ریست لیست قفل
  └─ ریست محدودیت

🔹 **لیست کاربران:**
• لیست ادمین
• لیست مالک
• لیست ویژه
• لیست معاف
• لیست بلاک

🔹 **لیست کلمات:**
• لیست فحش
• لیست کلمات غیر مجاز
• لیست مجاز

🔹 **سایر:**
• لیست تگ
• لیست متادیتا
• لیست قوانین
"""
            await message.reply(menu)
            return

        # لیست پاکسازی
        if msg_text == "لیست پاکسازی":
            if not await check_admin(group_guid, user_guid):
                await message.reply("❌ فقط ادمین و مالک می‌تونن استفاده کنند")
                return
            
            settings = await db.get_group_settings(group_guid)
            if not settings:
                await message.reply("❌ گروه فعال نیست")
                return
            
            # پاک کردن همه لیست‌ها
            lists_to_clear = [
                "profanity", "forbidden_words", "whitelist", "admins", "owners",
                "special", "muted", "exempt", "blocked", "fonts", "rules"
            ]
            
            for list_name in lists_to_clear:
                await db.clear_list(group_guid, list_name)
            
            await message.reply("✅ تمام لیست‌ها پاک شدند")
            return

        # لیست ریست
        if msg_text == "لیست ریست":
            if not await check_admin(group_guid, user_guid):
                await message.reply("❌ فقط ادمین و مالک می‌تونن استفاده کنند")
                return
            
            reset_menu = """
**🔄 منوی ریست**

1️⃣ ریست لیست قفل - برگرداندن تمام قفل‌ها به دیفالت
2️⃣ ریست محدودیت - حذف اخطارات، سکوت‌ها، بلاک‌ها
"""
            await message.reply(reset_menu)
            return

        if msg_text == "ریست لیست قفل":
            if not await check_admin(group_guid, user_guid):
                return
            
            if await db.reset_locks(group_guid):
                await message.reply("✅ تمام قفل‌ها ریست شدند")
            else:
                await message.reply("❌ خطا در ریست قفل‌ها")
            return

        if msg_text == "ریست محدودیت":
            if not await check_admin(group_guid, user_guid):
                return
            
            if await db.reset_restrictions(group_guid):
                await message.reply("✅ تمام محدودیت‌ها ریست شدند")
            else:
                await message.reply("❌ خطا در ریست محدودیت‌ها")
            return

        # لیست بلاک
        if msg_text == "لیست بلاک":
            if not await check_admin(group_guid, user_guid):
                return
            
            blocked_list = await db.get_list(group_guid, "blocked")
            if not blocked_list:
                await message.reply("📋 **لیست کاربران بلاک شده**\n\n❌ هیچ کاربری بلاک نشده")
                return
            
            text = "📋 **لیست کاربران بلاک شده**\n\n"
            for idx, user_guid in enumerate(blocked_list, 1):
                user_name = await db.get_user_display_name(group_guid, user_guid)
                text += f"{idx}. [{user_name}]({user_guid})\n"
            
            await message.reply(text)
            return

        # لیست معاف
        if msg_text == "لیست معاف":
            if not await check_admin(group_guid, user_guid):
                return
            
            exempt_list = await db.get_list(group_guid, "exempt")
            if not exempt_list:
                await message.reply("📋 **لیست کاربران معاف**\n\n❌ هیچ کاربری معاف نشده")
                return
            
            text = "📋 **لیست کاربران معاف**\n\n"
            for idx, user_guid in enumerate(exempt_list, 1):
                user_name = await db.get_user_display_name(group_guid, user_guid)
                text += f"{idx}. [{user_name}]({user_guid})\n"
            
            await message.reply(text)
            return

        # لیست ادمین
        if msg_text in ["لیست ادمین", "لیست مدیران"]:
            if not await check_admin(group_guid, user_guid):
                return
            
            admins = await db.get_group_admins(group_guid)
            if not admins:
                await message.reply("👮‍♂️ **لیست مدیران**\n\n❌ هیچ ادمینی وجود ندارد")
                return
            
            text = "👮‍♂️ **لیست مدیران**\n\n"
            for idx, admin in enumerate(admins, 1):
                admin_name = await db.get_user_display_name(group_guid, admin["user_guid"])
                text += f"{idx}. [{admin_name}]({admin['user_guid']})\n"
            
            await message.reply(text)
            return

        # لیست مالک
        if msg_text == "لیست مالک":
            owner = await db.get_group_owner_member(group_guid)
            if not owner:
                await message.reply("👑 **مالک گروه**\n\n❌ مالکی تعریف نشده")
                return
            
            owner_name = await db.get_user_display_name(group_guid, owner["user_guid"])
            text = f"👑 **مالک گروه**\n\n[{owner_name}]({owner['user_guid']})"
            await message.reply(text)
            return

        # لیست تگ
        if msg_text == "لیست تگ":
            if not await check_admin(group_guid, user_guid):
                return
            
            tags = await db.get_all_tags(group_guid)
            if not tags:
                await message.reply("🏷️ **لیست تگ‌ها**\n\n❌ هیچ تگی وجود ندارد")
                return
            
            text = "🏷️ **لیست تگ‌ها**\n\n"
            for idx, tag_name in enumerate(tags.keys(), 1):
                text += f"{idx}. {tag_name}\n"
            
            await message.reply(text)
            return

        # لیست مجاز
        if msg_text == "لیست مجاز":
            if not await check_admin(group_guid, user_guid):
                return
            
            whitelist = await db.get_list(group_guid, "whitelist")
            if not whitelist:
                await message.reply("✅ **لیست مجاز**\n\n❌ هیچ آیتمی مجاز نشده")
                return
            
            text = "✅ **لیست مجاز**\n\n"
            for idx, item in enumerate(whitelist, 1):
                text += f"{idx}. {item}\n"
            
            await message.reply(text)
            return

        # لیست فحش
        if msg_text == "لیست فحش":
            if not await check_admin(group_guid, user_guid):
                return
            
            profanity = await db.get_list(group_guid, "profanity")
            if not profanity:
                await message.reply("🚫 **لیست فحش**\n\n❌ هیچ کلمه‌ای وجود ندارد")
                return
            
            text = "🚫 **لیست فحش**\n\n"
            for idx, word in enumerate(profanity, 1):
                text += f"{idx}. {word}\n"
            
            await message.reply(text)
            return

        # لیست کلمات غیر مجاز
        if msg_text == "لیست کلمات غیر مجاز":
            if not await check_admin(group_guid, user_guid):
                return
            
            forbidden = await db.get_list(group_guid, "forbidden_words")
            if not forbidden:
                await message.reply("⛔ **لیست کلمات غیر مجاز**\n\n❌ هیچ کلمه‌ای وجود ندارد")
                return
            
            text = "⛔ **لیست کلمات غیر مجاز**\n\n"
            for idx, word in enumerate(forbidden, 1):
                text += f"{idx}. {word}\n"
            
            await message.reply(text)
            return

        # لیست قوانین
        if msg_text == "لیست قوانین":
            if not await check_admin(group_guid, user_guid):
                return
            
            rules = await db.get_group_rules(group_guid)
            if not rules:
                await message.reply("📜 **قوانین گروه**\n\n❌ هیچ قانونی تعریف نشده")
                return
            
            await message.reply(f"📜 **قوانین گروه**\n\n{rules}")
            return

        # لیست متادیتا
        if msg_text == "لیست متادیتا":
            if not await check_admin(group_guid, user_guid):
                return
            
            settings = await db.get_group_settings(group_guid)
            metadata = settings.get("lists", {}).get("metadata", {})
            
            text = "🎨 **متادیتا (فرمت‌های پیام)**\n\n"
            for format_name, is_locked in metadata.items():
                status = "🔒 قفل" if is_locked else "🔓 باز"
                text += f"• {format_name}: {status}\n"
            
            await message.reply(text)
            return
