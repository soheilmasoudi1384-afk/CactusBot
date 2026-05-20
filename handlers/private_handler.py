import asyncio
from rubpy import BotClient, Client
from rubpy.bot import filters
from rubpy.bot.models import Message, Keypad, KeypadRow, Button, Update, ChatKeypadTypeEnum, ButtonTypeEnum
from core import db
from utils.texts import *
import config
import aiohttp

# دیکشنری برای نگهداری وضعیت ادمین (جهت دریافت پست برای ارسال همگانی و دریافت ظرفیت)
admin_states = {}
started_users = {}

def register_private_handlers(bot: BotClient):
    texts = load_texts("locales/texts.json")

    async def send_rubika_menu(chat_id, text_message):
        """
        ارسال پیام همراه با کیبورد اختصاصی (راهنما و لیست دستورات) در روبیکا به صورت Async
        """
        bot_token = config.BOT_TOKEN
        url = f"https://botapi.rubika.ir/v3/{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text_message,
            "chat_keypad_type": "New",
            "chat_keypad": {
                "rows": [
                    {
                        "buttons": [
                            {"id": "btn_help", "type": "Simple", "button_text": "💡 راه اندازی ربات"},
                            {"id": "btn_commands", "type": "Simple", "button_text": "📃 راهنمای دستورات"}
                        ]
                    }
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
        }
        headers = {'Content-Type': 'application/json'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except:
            return None

    # --- تابع جدید برای ارسال منوی ادمین ---
    async def send_admin_menu(chat_id, text_message):
        bot_token = config.BOT_TOKEN
        url = f"https://botapi.rubika.ir/v3/{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text_message,
            "chat_keypad_type": "New",
            "chat_keypad": {
                "rows": [
                    {
                        "buttons": [
                            {"id": "a1", "type": "Simple", "button_text": "آمار گروه‌ها"},
                            {"id": "a2", "type": "Simple", "button_text": "آمار کاربران"}
                        ]
                    },
                    {
                        "buttons": [
                            {"id": "a3", "type": "Simple", "button_text": "ارسال پست به گروه‌ها"},
                            {"id": "a4", "type": "Simple", "button_text": "ارسال پست به کاربران"}
                        ]
                    },
                    {
                        "buttons": [
                            {"id": "a5", "type": "Simple", "button_text": "تنظیم کانال‌های اجباری"},
                            {"id": "a6", "type": "Simple", "button_text": "قفل پیوی ربات"}
                        ]
                    },
                    {
                        "buttons": [
                            {"id": "a7", "type": "Simple", "button_text": "تنظیم ظرفیت گروه‌ها"}
                        ]
                    },
                    {
                        "buttons": [
                            {"id": "a8", "type": "Simple", "button_text": "📅 ارسال دوره‌ای به گروه‌ها"},
                            {"id": "a9", "type": "Simple", "button_text": "📋 حذف پیام‌های دوره‌ای"}
                        ]
                    }
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
        }

        headers = {'Content-Type': 'application/json'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            print(f"Admin menu error: {e}")
            return None

    async def check_database(user_guid):
        if await db.get_user(user_guid) != None:
            pass
        else:
            await db.add_user(user_guid)

    async def check_channel_forced(user_guid):
        channels = await db.get_all_forced_channels()
        if len(channels) > 0:
            check = 0
            text = f"🔐 برای استفاده از بات به صورت دایمی و رایگان حتما در کانال های زیر عضو شوید.\n"
            for channel in channels:
                try:
                    x = await bot.get_chat_member(channel["channel_guid"], user_guid)
                    text += "\n" + channel["channel_id"]
                except Exception as e:
                    check = 1
            if check == 1:
                text += f"\n💡 پس از عضو شدن /start را ارسال کنید."
                return [0, text]
            else:
                return [1, "y"]
        else:
            return [1, "y"]

    async def check_pv_lock(user_guid, message: Update):
        if user_guid in config.ADMIN_GUIDS:
            return False
        is_locked = await db.get_pv_status()
        if is_locked:
            await message.reply(" 🔐 متاسفانه فعلا ظرفیت گروه های این ربات بدلیل اینکه کیفیت ربات حفظ بشه تکمیل شده ♨ لطفا از ربات دوم استفاده کنید(لینک ربات دوم داخل کانال ربات 👇 ) 🛃    @SajiAnti ")
            return True 
        return False

    # ----------------------------------------
    # هندلرهای عمومی (کاربران)
    # ----------------------------------------

    @bot.on_update(filters.private & filters.commands("start"))
    async def start_handler(client, message: Update):
        user_guid = message.chat_id
        await check_database(user_guid)
        if await check_pv_lock(user_guid, message):
            return
    
        i = await check_channel_forced(user_guid)
        if i[0] == 0:
            await message.reply(i[1])
            return
        
        # بررسی اینکه آیا کاربر برای اولین بار /start می‌زند
        if user_guid not in started_users:
            await send_rubika_menu(user_guid, t("first_start_bot", texts))
            # علامت‌گذاری که کاربر استارت زده
            started_users[user_guid] = True
        else:
            # پیام عادی برای دفعات بعدی
            await send_rubika_menu(user_guid, t("start_bot", texts))
        
            # ----------------------------------------

    @bot.on_update(filters.private & filters.commands("guid"))
    async def get_guid_handler(client, message: Update):
        user_guid = message.chat_id
        await check_database(user_guid)
        if await check_pv_lock(user_guid, message):
            return

        i = await check_channel_forced(user_guid)
        if i[0] == 0:
            await message.reply(i[1])
            return

        await message.reply(user_guid)

    @bot.on_update(filters.private & filters.text("💡 راه اندازی ربات"))
    async def help_handler(client, message: Update):
        user_guid = message.chat_id
        await check_database(user_guid)
        
        if await check_pv_lock(user_guid, message):
            return

        i = await check_channel_forced(user_guid)
        if i[0] == 0:
            await message.reply(i[1])
            return
            
        await message.reply(t("help_command", texts))
        

    @bot.on_update(filters.private & filters.text("📃 راهنمای دستورات"))
    async def list_handler(client, message: Update):
        user_guid = message.chat_id
        await check_database(user_guid)
        
        if await check_pv_lock(user_guid, message):
            return

        i = await check_channel_forced(user_guid)
        if i[0] == 0:
            await message.reply(i[1])
            return
            
        await message.reply(t("list_command", texts))

    # ----------------------------------------
    # هندلرهای بخش مدیریت (فقط ادمین ها)
    # ----------------------------------------

    @bot.on_update(filters.private & filters.commands("admin"))
    async def admin_panel_handler(client, message: Update):
        user_guid = message.chat_id
        if user_guid not in config.ADMIN_GUIDS:
            return
            
        admin_text = "👑 **پنل مدیریت ربات**\n\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:"
        
        # فراخوانی تابع ارسال دکمه‌های ادمین
        await send_admin_menu(user_guid, admin_text)

    # هندلر پیام‌های متنی ادمین
    @bot.on_update(filters.private)
    async def admin_text_commands(client, message: Update):
        user_guid = message.chat_id
        if user_guid not in config.ADMIN_GUIDS:
            return
            
        text = message.new_message.text or ""

        # --- بخش بررسی وضعیت (State ها) ---
        if user_guid in admin_states:
            state = admin_states[user_guid]
            
            # --- وضعیت دریافت عدد برای تنظیم ظرفیت ---
            if state == "set_capacity":
                try:
                    capacity = int(text)
                    await db.set_group_capacity(capacity)
                    del admin_states[user_guid] # حذف وضعیت
                    await message.reply(f"✅ ظرفیت مجاز گروه‌ها با موفقیت روی {capacity} تنظیم شد.")
                except ValueError:
                    await message.reply("❌ خطا: لطفا فقط یک عدد صحیح و معتبر وارد کنید (مثلاً: 50).")
                return

            # --- وضعیت دریافت پست برای فوروارد همگانی ---
            elif state in ["broadcast_groups", "broadcast_users"]:
                await message.reply("در حال ارسال پست... لطفا صبور باشید ⏳\nبسته به تعداد مخاطبین ممکن است زمان ببرد.")
                
                if state == "broadcast_groups":
                    targets = await db.get_all_groups()
                    target_guids = [g["group_guid"] for g in targets]
                else: 
                    targets = await db.get_all_users()
                    users2 = []
                    for i in targets: # اصلاح نام متغیر users به targets
                        if i["user_guid"][0] == "b":
                            users2.append(i)
                    target_guids = [u["user_guid"] for u in users2]
                    
                success_count = 0
                fail_count = 0
                
                for target_guid in target_guids:
                    try:
                        await bot.forward_message(user_guid, message.new_message.message_id, target_guid)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                    
                    await asyncio.sleep(0.3)
                
                del admin_states[user_guid]
                await message.reply(f"✅ ارسال همگانی با موفقیت پایان یافت!\n\nارسال موفق: {success_count}\nارسال ناموفق: {fail_count}")
                return
            # Handle scheduled broadcast states
            elif state == "scheduled_broadcast_message":
                admin_states[user_guid] = f"scheduled_broadcast_interval:{message.new_message.message_id}"
                await bot.send_message(
                    user_guid,
                    "پیام ذخیره شد. حالا فاصله زمانی ارسال را به ساعت وارد کنید (مثال: 8)"
                )
                return

            elif state and state.startswith("scheduled_broadcast_interval:"):
                msg_id = state.split(":")[1]
                try:
                    interval = int(text)
                    if interval < 1:
                        raise ValueError
                    
                    await db.get_all_scheduled_messages()
                    await db.add_scheduled_message(msg_id, interval)
                    await bot.send_message(
                        user_guid,
                        f"✅ پیام با موفقیت تنظیم شد!\n\n🆔 Message ID: `{msg_id}`\n⏰ هر {interval} ساعت به تمام گروه‌ها فوروارد می‌شود."
                    )
                    del admin_states[user_guid]
                except ValueError:
                    await bot.send_message(user_guid, "❌ لطفا یک عدد صحیح بزرگتر از 0 وارد کنید.")
                return
        
        # --- بخش دستورات متنی / دکمه‌های ادمین ---
        if text == "آمار گروه‌ها":
            groups = await db.get_all_groups()
            await message.reply(f"📊 **آمار گروه‌های ربات:**\n\nتعداد گروه‌های ثبت شده: {len(groups)} گروه 🚀\nربات با قدرت در حال مدیریت گروه‌هاست! 🛡")
            
        elif text == "آمار کاربران":
            users = await db.get_all_users()
            users2 = []
            for i in users:
                if i["user_guid"][0] == "b":
                    users2.append(i)
            await message.reply(f"👥 **آمار کاربران ربات:**\n\nتعداد کاربرانی که ربات را در پیوی استارت زده‌اند: {len(users2)} نفر 👤\n(کاربران گروه‌ها محاسبه نشده‌اند)")
            
        elif text == "ارسال پست به گروه‌ها":
            admin_states[user_guid] = "broadcast_groups"
            await message.reply("لطفا پستی که می‌خواهید به تمام گروه‌ها فوروارد شود را الان ارسال کنید (متن، عکس، فیلم، ویس و...):")
            
        elif text == "ارسال پست به کاربران":
            admin_states[user_guid] = "broadcast_users"
            await message.reply("لطفا پستی که می‌خواهید به پیوی تمام کاربران فوروارد شود را الان ارسال کنید:")
            
        elif text == "تنظیم کانال‌های اجباری":
            await message.reply("این بخش فعلا در دسترس نمیباشد ❌")
            
        elif text == "قفل پیوی ربات":
            current_status = await db.get_pv_status()
            new_status = not current_status
            await db.set_pv_status(new_status)
            
            if new_status:
                await message.reply("🔒 پیوی ربات قفل شد (خاموش).\nاز این پس کاربران عادی پیام خاموش بودن ربات را دریافت می‌کنند.")
            else:
                await message.reply("🔓 پیوی ربات باز شد (روشن).")
                
        # وقتی ادمین روی دکمه "تنظیم ظرفیت گروه‌ها" کلیک کند
        elif text == "تنظیم ظرفیت گروه‌ها":
            admin_states[user_guid] = "set_capacity"
            await message.reply("⚙️ لطفا ظرفیت جدیدی که برای گروه‌ها مد نظر دارید را به صورت یک **عدد** ارسال کنید:\n(برای لغو میتوانید روی دستورات دیگر کلیک کنید)")
        elif text == "📅 ارسال دوره‌ای به گروه‌ها":
            admin_states[user_guid] = "scheduled_broadcast_message"
            await bot.send_message(
                user_guid,
                "لطفا پیامی که می‌خواهید به صورت دوره‌ای به تمام گروه‌ها فوروارد شود را ارسال کنید..."
            )
            return

        elif text == "📋 حذف پیام‌های دوره‌ای":
            await db.get_all_scheduled_messages()
            await message.reply("با موفقیت پیام دوره ای حذف شد.")
            return
        