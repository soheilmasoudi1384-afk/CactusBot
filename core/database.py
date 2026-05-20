import aiomysql
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import random

# تعریف ساختار پیش‌فرض برای تنظیمات گروه جهت خوانایی و استفاده آسان
DEFAULT_GROUP_SETTINGS = {
    "locks": {
        "text": False, "link": True, "sticker": False,
        "photo": False, "video": False, "voice": False, "file": False,
        "gif": False, "music": False, "profanity": False, "forbidden_words": False,
        "english_text": False, "reply": False, "forward": True, "edit": False,
        "emoji": False, "hang_code": True, "poll": False, "phone_number": False,
        "number": False, "hashtag": False, "warning": False
    },
    "features": {
        "spokesperson_panel": True, "group_stats": True, "user_stats": True, "entertainment": True
    },
    "lists": {
        "profanity": [], # لیست پیش‌فرض کلمات رکیک
        "forbidden_words": [],
        "reports": {
            "text": 0, "photo": 0, "video": 0, "sticker": 0
            },
        "exempt_users": []
    },
    "max_warnings" : 3,
    "kicked" : 0,
    "welcome": False,
    "welcome_message" : "سلام عزیز 🌹\nبه گروه خوش اومدی!\nامیدواریم لحظات خوبی رو کنار ما داشته باشی. لطفاً برای حفظ نظم، قوانین رو رعایت کن. 🙏",
    "mute_group": 0
}


class Database:
    """MySQL database manager for Rubika group management"""
    
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.pool: Optional[aiomysql.Pool] = None
        
    
    async def connect(self):
        """Connect to MySQL and create tables if they don't exist"""
        self.pool = await aiomysql.create_pool(
            host=self.host, port=self.port, user=self.user,
            password=self.password, db=self.database,
            autocommit=True, charset='utf8mb4'
        )
        await self._create_tables()
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def _create_tables(self):
        """Create necessary tables safely"""
        
        tables_to_create = {
            "groups": """
                CREATE TABLE `groups` (
                    group_guid VARCHAR(255) PRIMARY KEY,
                    title VARCHAR(500),
                    member_count INT DEFAULT 0,
                    settings JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """,
            "users": """
                CREATE TABLE users (
                    user_guid VARCHAR(255) PRIMARY KEY
                )
            """,
            "group_members": """
                CREATE TABLE group_members (
                    group_guid VARCHAR(255),
                    user_guid VARCHAR(255),
                    message_count BIGINT DEFAULT 0,
                    messages_today INT DEFAULT 0,
                    warning INT DEFAULT 0,
                    mute INT DEFAULT 0,
                    user_rank VARCHAR(50) DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_guid, user_guid),
                    FOREIGN KEY (group_guid) REFERENCES `groups`(group_guid) ON DELETE CASCADE,
                    FOREIGN KEY (user_guid) REFERENCES users(user_guid) ON DELETE CASCADE
                )
            """,
            "warnings": """
                CREATE TABLE warnings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_guid VARCHAR(255),
                    user_guid VARCHAR(255),
                    reason TEXT,
                    warned_by VARCHAR(255),
                    warned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_group_user (group_guid, user_guid)
                )
            """,
            
            "forced_channels": """
                CREATE TABLE forced_channels (
                    channel_guid VARCHAR(255) PRIMARY KEY,
                    channel_id VARCHAR(255) UNIQUE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,

            "bot_settings": """
                CREATE TABLE bot_settings (
                    id INT PRIMARY KEY DEFAULT 1,
                    pv_locked BOOLEAN DEFAULT FALSE,
                    max_groups INT DEFAULT 50
                )
            """,
            "user_scores": """
                CREATE TABLE user_scores (
                    group_guid      VARCHAR(255) NOT NULL,
                    user_guid       VARCHAR(255) NOT NULL,
                    user_information JSON,
                    score           INT DEFAULT 0,
                    PRIMARY KEY (group_guid, user_guid)
                );
            """,
            "scheduled_messages": """
                CREATE TABLE IF NOT EXISTS scheduled_messages (
                    message_id VARCHAR(255) PRIMARY KEY,
                    interval_hours INT NOT NULL,
                    last_sent DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """

        }

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES")
                existing_tables = [row[0] for row in await cursor.fetchall()]

                for table_name, create_query in tables_to_create.items():
                    if table_name not in existing_tables:
                        await cursor.execute(create_query)

    
    # ===== Group Methods =====
    async def add_or_update_group(self, group_guid: str, title: str):
        """Adds a new group with default settings or updates its title if it exists."""
        settings_json = json.dumps(DEFAULT_GROUP_SETTINGS)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO `groups` (group_guid, title, settings)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE title = VALUES(title)
                """, (group_guid, title, settings_json))

    async def get_group_settings(self, group_guid: str) -> Optional[Dict]:
        """Get group settings"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT settings FROM `groups` WHERE group_guid = %s", (group_guid,))
                result = await cursor.fetchone()
                if result and result.get('settings'):
                    return json.loads(result['settings'])
                return None
    
    async def update_group_settings(self, group_guid: str, settings: dict):
        """Update the entire settings object for a group."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE `groups` SET settings = %s WHERE group_guid = %s",
                    (json.dumps(settings), group_guid)
                )

    # ===== Group Member Methods =====
    async def add_user_to_group(self, group_guid: str, user_guid: str, user_rank: str = 'member'):
        """Adds a user to a group's member list."""
        # ابتدا اطمینان حاصل می‌کنیم کاربر در جدول اصلی users وجود دارد
        await self.add_user(user_guid)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT IGNORE INTO group_members (group_guid, user_guid, user_rank)
                    VALUES (%s, %s, %s)
                """, (group_guid, user_guid, user_rank))

    async def get_group_member(self, group_guid: str, user_guid: str) -> Optional[Dict]:
        """Retrieves a specific user's data for a specific group."""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # برای تعداد اخطارها، به صورت زنده از جدول warnings شمارش می‌کنیم
                await cursor.execute("""
                    SELECT 
                        gm.*, 
                        (SELECT COUNT(*) FROM warnings w WHERE w.group_guid = gm.group_guid AND w.user_guid = gm.user_guid) AS warnings_count
                    FROM 
                        group_members gm
                    WHERE 
                        gm.group_guid = %s AND gm.user_guid = %s
                """, (group_guid, user_guid))
                return await cursor.fetchone()
            
    async def decrement_all_muted_groups(self):
        """
        Decrease mute_group count by 1 for ALL groups where mute_group > 0.
        This is highly optimized and runs a single query.
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        UPDATE `groups`
                        SET settings = JSON_SET(settings, '$.mute_group', 
                            GREATEST(JSON_EXTRACT(settings, '$.mute_group') - 1, 0))
                        WHERE JSON_EXTRACT(settings, '$.mute_group') > 0
                    """)
        except Exception as e:
            print(f"Database Error in decrement_all_muted_groups: {e}")
    
    async def decrement_all_mutes(self):
        """
        Decrease mute count by 1 for ALL users who are currently muted.
        This is highly optimized and runs a single query.
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        UPDATE group_members
                        SET mute = mute - 1
                        WHERE mute > 0
                    """)
                await conn.commit()
        except Exception as e:
            print(f"Database Error in decrement_all_mutes: {e}")

    
    async def set_member_mute(self, group_guid: str, user_guid: str, mute_count: int):
        """
        Set mute count for a user in a specific group.
        If mute_count is 0, user is unmuted.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET mute = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (mute_count, group_guid, user_guid))

    async def get_group_total_messages(self, group_guid: str) -> int:
        """
        مجموع پیام‌های ارسال شده توسط تمامی اعضای یک گروه را محاسبه می‌کند.
        
        Parameters:
            group_guid (str): شناسه گروه
            
        Returns:
            int: مجموع پیام‌های گروه
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT SUM(message_count) 
                    FROM group_members 
                    WHERE group_guid = %s
                """, (group_guid,))
                result = await cursor.fetchone()
                
                return int(result[0]) if result and result[0] is not None else 0
            
    async def get_group_total_messages_today(self, group_guid: str) -> int:
        """
        مجموع پیام‌های ارسال شده توسط تمامی اعضای 24 ساعت اخیر را محاسبه می‌کند.
        
        Parameters:
            group_guid (str): شناسه گروه
            
        Returns:
            int: مجموع پیام‌های گروه
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT SUM(messages_today) 
                    FROM group_members 
                    WHERE group_guid = %s
                """, (group_guid,))
                result = await cursor.fetchone()
                
                return int(result[0]) if result and result[0] is not None else 0
    
    async def get_muted_members_count(self, group_guid: str):
        """
        Returns the number of group members whose mute_count is greater than 0.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT COUNT(*) 
                    FROM group_members
                    WHERE group_guid = %s AND mute > 0
                """, (group_guid,))
                
                (count,) = await cursor.fetchone()
                return count

    
    async def decrement_member_mute(self, group_guid: str, user_guid: str):
        """
        Decrease mute count by 1.
        Mute value will never go below 0.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET mute = CASE 
                        WHEN mute > 0 THEN mute - 1 
                        ELSE 0 
                    END
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))


    async def is_member_muted(self, group_guid: str, user_guid: str) -> bool:
        """
        Check if user is currently muted.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT mute FROM group_members
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
                result = await cursor.fetchone()
                return bool(result and result[0] > 0)
            
    async def get_group_members(self, group_guid: str) -> List[Dict]:
        """Get all members of a group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT DISTINCT user_guid FROM group_members WHERE group_guid = %s",
                    (group_guid,)
                )
                return await cursor.fetchall()
            
    async def get_member_mute(self, group_guid: str, user_guid: str) -> int:
        """
        Get current mute count of a user in a group.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT mute FROM group_members
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
                result = await cursor.fetchone()
                return result[0] if result else 0

        # ===== User Rank Methods =====
    async def get_group_admins(self, group_guid: str) -> List[Dict]:
        """
        دریافت لیست تمامی ادمین‌های یک گروه (کسانی که user_rank آنها admin است).
        
        Parameters:
            group_guid (str): شناسه گروه
            
        Returns:
            List[Dict]: لیستی از دیکشنری‌ها شامل اطلاعات ادمین‌ها
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, user_rank 
                    FROM group_members 
                    WHERE group_guid = %s AND user_rank = 'admin'
                """, (group_guid,))
                
                result = await cursor.fetchall()
                return list(result) if result else []
            

    async def set_user_rank(self, group_guid: str, user_guid: str, rank: str) -> bool:
        """
        Set or update the rank of a user in a specific group.
        
        Parameters:
            group_guid (str): Group identifier
            user_guid (str): User identifier
            rank (str): New rank value (e.g., 'member', 'admin', 'moderator', 'owner')
            
        Returns:
            bool: True if update was successful, False if user not found in group
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members 
                    SET user_rank = %s 
                    WHERE group_guid = %s AND user_guid = %s
                """, (rank, group_guid, user_guid))
                
                # بررسی تعداد ردیف‌های تأثیرپذیر
                return cursor.rowcount > 0


    async def increment_user_message_count(self, group_guid: str, user_guid: str):
        """Increments total and daily message counts for a user in a group."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET message_count = message_count + 1, messages_today = messages_today + 1
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
    
    async def increment_member_warning(self, group_guid: str, user_guid: str):
        """Increase user's warning count inside group_members table by +1."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET warning = warning + 1
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
    
    async def set_member_warning(self, group_guid: str, user_guid: str, count: int):
        """Set the user's warning count to an exact number (including reset to 0)."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET warning = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (count, group_guid, user_guid))


                
    async def reset_daily_messages(self):
        """Resets the daily message count for ALL users in ALL `groups`.
        This should be run once a day by a scheduler."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE group_members SET messages_today = 0")

    # متدهای مربوط به اخطار، سکوت و بلاک مانند قبل باقی می‌مانند
    # ... (add_warning, get_warnings, etc)

    
    # User methods (تغییرات اصلی در این بخش اعمال شده است)
    async def add_user(self, user_guid: str):
        """Add user (if not exists)"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # استفاده از IGNORE برای جلوگیری از خطا در صورت وجود کاربر
                await cursor.execute("""
                    INSERT IGNORE INTO users (user_guid)
                    VALUES (%s)
                """, (user_guid,))
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users from database"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users")
                result = await cursor.fetchall()
                # تبدیل نتیجه به لیست (در صورت خالی بودن، لیست خالی برمی‌گرداند)
                return list(result) if result else []
    
    async def get_user(self, user_guid: str) -> Optional[Dict]:
        """Get user"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users WHERE user_guid = %s", (user_guid,))
                return await cursor.fetchone()
    
        # ===== Forced Join Methods =====

    async def get_top3_active_members(self, group_guid: str):
        """
        Returns exactly 3 members.
        If fewer than 3 members exist, fills empty slots with '-' values.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, messages_today
                    FROM group_members
                    WHERE group_guid = %s
                    ORDER BY messages_today DESC
                """, (group_guid,))
                
                members = await cursor.fetchall()

                # اگر گروه خالی بود → سه جای خالی برگردان
                if not members:
                    return [
                        {"user_guid": "-", "messages_today": "-"},
                        {"user_guid": "-", "messages_today": "-"},
                        {"user_guid": "-", "messages_today": "-"}
                    ]

                # گروه‌بندی برای موارد مساوی
                grouped = {}
                for m in members:
                    grouped.setdefault(m["messages_today"], []).append(m)

                sorted_counts = sorted(grouped.keys(), reverse=True)

                top_members = []
                for count in sorted_counts:
                    users_with_same = grouped[count]
                    random.shuffle(users_with_same)  # انتخاب تصادفی در صورت مساوی
                    
                    for u in users_with_same:
                        if len(top_members) < 3:
                            top_members.append(u)
                        else:
                            break
                    if len(top_members) >= 3:
                        break

                # اگر کمتر از 3 نفر بود → با "-" پر کن
                while len(top_members) < 3:
                    top_members.append({
                        "user_guid": "-",
                        "messages_today": "-"
                    })

                return top_members

    async def add_forced_channel(self, channel_guid: str, channel_id: str):
        """
        اضافه کردن کانال برای جوین اجباری.
        اگر کانال از قبل وجود داشته باشد، آیدی آن آپدیت می‌شود.
        """
        # حذف @ از ابتدای آیدی در صورت وجود، برای یکپارچگی داده‌ها
        # clean_channel_id = channel_id.replace("@", "") 
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO forced_channels (channel_guid, channel_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
                """, (channel_guid, channel_id))

    async def get_all_forced_channels(self) -> List[Dict]:
        """
        دریافت لیست تمام کانال‌های جوین اجباری به همراه GUID و آیدی کانال.
        خروجی: لیستی از دیکشنری‌ها شامل {'channel_guid': '...', 'channel_id': '...'}
        """
        async with self.pool.acquire() as conn:
            # استفاده از DictCursor برای برگرداندن نتیجه به صورت دیکشنری
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # انتخاب هر دو ستون مورد نیاز
                await cursor.execute("SELECT channel_guid, channel_id FROM forced_channels")
                result = await cursor.fetchall()
                
                # برگرداندن لیست نتایج یا یک لیست خالی در صورت نبود رکورد
                return list(result) if result else []
            
    # دریافت کل گروه ها برای آمار و ارسال همگانی
    async def get_all_groups(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT group_guid FROM `groups`")
                result = await cursor.fetchall()
                return list(result) if result else []

    # دریافت کل کاربران پیوی
        # دریافت کل کاربران (برای ارسال همگانی به پیوی)
    async def get_all_users(self) -> list:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT user_guid FROM users")
                rows = await cursor.fetchall()
                return [{"user_guid": row[0]} for row in rows] if rows else []

    
    # دریافت وضعیت قفل پیوی
    async def get_pv_status(self) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT pv_locked FROM bot_settings WHERE id = 1")
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    # تغییر وضعیت قفل پیوی
    async def set_pv_status(self, status: bool):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # اگر آیدی ۱ نبود میسازد، اگر بود آپدیت میکند
                await cursor.execute("""
                    INSERT INTO bot_settings (id, pv_locked) 
                    VALUES (1, %s) 
                    ON DUPLICATE KEY UPDATE pv_locked = VALUES(pv_locked)
                """, (int(status),))
                await conn.commit()

    # تنظیم ظرفیت گروه ها
    async def set_group_capacity(self, capacity: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # اگر آیدی ۱ نبود میسازد، اگر بود آپدیت میکند
                await cursor.execute("""
                    INSERT INTO bot_settings (id, max_groups) 
                    VALUES (1, %s) 
                    ON DUPLICATE KEY UPDATE max_groups = VALUES(max_groups)
                """, (capacity,))
                await conn.commit()
    
        # دریافت ظرفیت تنظیم شده برای گروه‌ها
    async def get_group_capacity(self) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT max_groups FROM bot_settings WHERE id = 1")
                result = await cursor.fetchone()
                # اگر مقداری در دیتابیس بود آن را برمی‌گرداند، در غیر این صورت مقدار پیش‌فرض 500 را برمی‌گرداند
                return int(result[0]) if result else 500

    async def remove_forced_channel_by_id(self, channel_id: str):
        """
        حذف یک کانال از لیست جوین اجباری با استفاده از آیدی کانال.
        """
        # clean_channel_id = channel_id.replace("@", "")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM forced_channels WHERE channel_id = %s",
                    (channel_id,)
                )

    async def set_user_score_info(self, group_guid, user_guid, user_information=None, score=0):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO user_scores (group_guid, user_guid, user_information, score)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        user_information = VALUES(user_information),
                        score = VALUES(score)
                """, (group_guid, user_guid, json.dumps(user_information), score))
                await conn.commit()

    async def update_user_information(self, group_guid, user_guid, user_information):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE user_scores
                    SET user_information = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (json.dumps(user_information), group_guid, user_guid))
                await conn.commit()


    async def update_user_score(self, group_guid, user_guid, score):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE user_scores
                    SET score = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (score, group_guid, user_guid))
                await conn.commit()


    async def increment_user_score(self, group_guid, user_guid, delta=1):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO user_scores (group_guid, user_guid, score)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        score = score + VALUES(score)
                """, (group_guid, user_guid, delta))
                await conn.commit()


    async def get_user_score_info(self, group_guid, user_guid):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_information, score
                    FROM user_scores
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
                row = await cursor.fetchone()

        if not row:
            return None

        user_information = None
        if row["user_information"]:
            try:
                user_information = json.loads(row["user_information"])
            except Exception:
                user_information = None

        return {
            "user_information": user_information,
            "score": row["score"],
        }


    async def get_all_user_scores(self, group_guid):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, user_information, score
                    FROM user_scores
                    WHERE group_guid = %s
                """, (group_guid,))
                rows = await cursor.fetchall()

        return rows

    async def get_top3_by_score(self, group_guid: str):
        """
        Returns exactly 3 members by score for a specific group.
        If fewer than 3 members exist, fills empty slots with '-' values.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, score
                    FROM user_scores
                    WHERE group_guid = %s
                    ORDER BY score DESC
                    LIMIT 3
                """, (group_guid,))
                rows = await cursor.fetchall()

        top_members = []

        for row in rows:
            top_members.append({
                "user_guid": row["user_guid"],
                "score": row["score"],
            })

        while len(top_members) < 3:
            top_members.append({
                "user_guid": "-",
                "score": 0,
            })

        return top_members[:3]
    
    async def add_scheduled_message(self, message_id: str, interval_hours: int):
        """Add or update scheduled message"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # حذف پیام قبلی
                await cursor.execute("DELETE FROM scheduled_messages")
                # اضافه کردن پیام جدید
                await cursor.execute(
                    """INSERT INTO scheduled_messages (message_id, interval_hours, last_sent)
                    VALUES (%s, %s, NULL)""",
                    (message_id, interval_hours)
                )
                await conn.commit()

    async def get_scheduled_messages(self) -> List[Dict]:
        """Get all scheduled messages that need to be sent"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT message_id, interval_hours, last_sent 
                    FROM scheduled_messages
                    WHERE last_sent IS NULL 
                        OR TIMESTAMPDIFF(HOUR, last_sent, NOW()) >= interval_hours"""
                )
                return await cursor.fetchall()

    async def update_scheduled_message_sent(self, message_id: str):
        """Update last_sent timestamp for a scheduled message"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE scheduled_messages SET last_sent = NOW() WHERE message_id = %s",
                    (message_id,)
                )
                await conn.commit()

    async def get_all_scheduled_messages(self) -> List[Dict]:
        """Get all scheduled messages for display"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT message_id, interval_hours, last_sent, created_at FROM scheduled_messages"
                )
                return await cursor.fetchall()

    async def delete_all_scheduled_messages(self):
        """Delete all scheduled messages"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM scheduled_messages")
                await conn.commit()



