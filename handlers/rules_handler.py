"""
Rules Handler for Group Management
هندلر مدیریت قوانین در گروه‌ها
"""
import asyncio
from rubpy.bot import filters
from rubpy.bot.models import Update
from modules.rules import RulesManager
from core import db

def register_rules_handlers(bot):
    """ثبت هندلرهای مربوط به قوانین"""
    
    rules_manager = RulesManager()
    
    # دیکشنری برای نگهداری وضعیت کاربران هنگام تنظیم قوانین
    rules_states = {}
    
    @bot.on_update(filters.group & filters.text("قوانین"))
    async def show_rules_handler(client, message: Update):
        """
        نمایش قوانین گروه
        """
        group_guid = message.chat_id
        
        rules = await rules_manager.get_rules(group_guid)
        
        if rules:
            await message.reply(f"📋 **قوانین گروه:**\n\n{rules}")
        else:
            await message.reply("❌ هنوز قوانینی برای این گروه تنظیم نشده است.")
    
    @bot.on_update(filters.group & filters.commands("set_rules"))
    async def set_rules_command(client, message: Update):
        """
        دستور تنظیم قوانین (فقط ادمین)
        """
        group_guid = message.chat_id
        user_guid = message.from_user_id
        
        # بررسی اینکه کاربر ادمین گروه است
        try:
            member = await db.get_group_member(group_guid, user_guid)
            
            if not member or member.get('user_rank') != 'admin':
                await message.reply("❌ فقط ادمین‌های گروه می‌توانند قوانین را تنظیم کنند.")
                return
        except Exception as e:
            print(f"Error checking admin status: {e}")
            await message.reply("❌ خطا در بررسی سطح دسترسی.")
            return
        
        # ورود به وضعیت انتظار دریافت قوانین
        rules_states[user_guid] = group_guid
        await message.reply("✏️ لطفا قوانین جدید را ارسال کنید:\n(شما می‌توانید چندین خط ارسال کنید)")
    
    @bot.on_update(filters.group & filters.text)
    async def handle_rules_input(client, message: Update):
        """
        دریافت متن قوانین از ادمین
        """
        user_guid = message.from_user_id
        group_guid = message.chat_id
        
        # اگر این کاربر در حالت تنظیم قوانین است
        if user_guid in rules_states and rules_states[user_guid] == group_guid:
            rules_text = message.new_message.text or ""
            
            if not rules_text.strip():
                await message.reply("❌ لطفا قوانین خالی ارسال نکنید.")
                return
            
            # ذخیره قوانین
            success = await rules_manager.set_rules(group_guid, rules_text)
            
            if success:
                await message.reply("✅ قوانین گروه با موفقیت به‌روز شد!")
                del rules_states[user_guid]
            else:
                await message.reply("❌ خطا در ذخیره قوانین.")
    
    @bot.on_update(filters.group & filters.commands("delete_rules"))
    async def delete_rules_command(client, message: Update):
        """
        حذف قوانین گروه (فقط ادمین)
        """
        group_guid = message.chat_id
        user_guid = message.from_user_id
        
        # بررسی اینکه کاربر ادمین است
        try:
            member = await db.get_group_member(group_guid, user_guid)
            
            if not member or member.get('user_rank') != 'admin':
                await message.reply("❌ فقط ادمین‌های گروه می‌توانند قوانین را حذف کنند.")
                return
        except Exception as e:
            print(f"Error checking admin status: {e}")
            await message.reply("❌ خطا در بررسی سطح دسترسی.")
            return
        
        success = await rules_manager.delete_rules(group_guid)
        
        if success:
            await message.reply("✅ قوانین گروه حذف شد.")
        else:
            await message.reply("❌ خطا در حذف قوانین.")
