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
        "number": False, "hashtag": False, "warning": False, "metadata": False, "id": False
    },
    "features": {
        "spokesperson_panel": True, "group_stats": True, "user_stats": True, "entertainment": True
    },
    "lists": {
        "profanity": [],
        "forbidden_words": [],
        "whitelist": [],
        "admins": [],
        "owners": [],
        "special": [],
        "muted": [],
        "exempt": [],
        "blocked": [],
        "tags": {"admin": True, "special": True, "owner": True, "exempt": True, "muted": True, "kick": True, "blocked": True},
        "metadata": {"hyperlink": False, "spoiler": False, "bold": False, "italic": False, "mono": False, "strikethrough": False, "underline": False, "quote": False},
        "fonts": [],
        "entertainment": {"chistan": False, "joke": False, "quiz": False},
        "utility": {"link": None},
        "rules": [],
        "reports": {
            "text": 0, "link": 0, "profanity": 0, "video": 0, "id": 0, "forbidden_words": 0,
            "voice": 0, "photo": 0, "forward": 0, "hang_code": 0, "sticker": 0, "poll": 0,
            "metadata": 0, "music": 0, "file": 0, "gif": 0
        }
    },
    "max_warnings": 3,
    "kicked": 0,
    "welcome": False,
    "welcome_message": "سلام عزیز 🌹\nبه گروه خوش اومدی!",
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
                    owner_guid VARCHAR(255),
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
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    username VARCHAR(255),
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
            "group_stats": """
                CREATE TABLE group_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_guid VARCHAR(255),
                    stat_type VARCHAR(50),
                    count INT DEFAULT 0,
                    recorded_date DATE,
                    recorded_time TIME,
                    UNIQUE KEY unique_stat (group_guid, stat_type, recorded_date),
                    FOREIGN KEY (group_guid) REFERENCES `groups`(group_guid) ON DELETE CASCADE
                )
            """,
            "user_daily_stats": """
                CREATE TABLE user_daily_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_guid VARCHAR(255),
                    user_guid VARCHAR(255),
                    message_count INT DEFAULT 0,
                    recorded_date DATE,
                    UNIQUE KEY unique_user_stat (group_guid, user_guid, recorded_date),
                    FOREIGN KEY (group_guid) REFERENCES `groups`(group_guid) ON DELETE CASCADE
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
                )
            """,
            "rules": """
                CREATE TABLE rules (
                    group_guid VARCHAR(255) PRIMARY KEY,
                    rules_text LONGTEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_guid) REFERENCES `groups`(group_guid) ON DELETE CASCADE
                )
            """,
            "scheduled_messages": """
                CREATE TABLE IF NOT EXISTS scheduled_messages (
                    message_id VARCHAR(255) PRIMARY KEY,
                    interval_hours INT NOT NULL,
                    last_sent DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "welcome_logs": """
                CREATE TABLE welcome_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_guid VARCHAR(255),
                    user_guid VARCHAR(255),
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_welcome (group_guid, user_guid)
                )
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
    async def add_or_update_group(self, group_guid: str, title: str, owner_guid: str = None):
        """Adds a new group with default settings or updates its title if it exists."""
        settings_json = json.dumps(DEFAULT_GROUP_SETTINGS)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if owner_guid:
                    await cursor.execute("""
                        INSERT INTO `groups` (group_guid, title, owner_guid, settings)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE title = VALUES(title), owner_guid = VALUES(owner_guid)
                    """, (group_guid, title, owner_guid, settings_json))
                else:
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

    async def get_group_owner(self, group_guid: str) -> Optional[str]:
        """Get group owner guid"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT owner_guid FROM `groups` WHERE group_guid = %s", (group_guid,))
                result = await cursor.fetchone()
                return result[0] if result else None

    # ===== List Management Methods =====
    async def add_to_list(self, group_guid: str, list_name: str, item: str):
        """Add item to a list in group settings"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        list_path = f"lists.{list_name}"
        if list_name not in settings.get("lists", {}):
            settings["lists"][list_name] = []
        
        if item not in settings["lists"][list_name]:
            settings["lists"][list_name].append(item)
            await self.update_group_settings(group_guid, settings)
            return True
        return False

    async def remove_from_list(self, group_guid: str, list_name: str, item: str):
        """Remove item from a list in group settings"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        if list_name in settings.get("lists", {}) and item in settings["lists"][list_name]:
            settings["lists"][list_name].remove(item)
            await self.update_group_settings(group_guid, settings)
            return True
        return False

    async def get_list(self, group_guid: str, list_name: str) -> List:
        """Get a specific list from group settings"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return []
        return settings.get("lists", {}).get(list_name, [])

    async def clear_list(self, group_guid: str, list_name: str):
        """Clear a specific list in group settings"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        if list_name in settings.get("lists", {}):
            settings["lists"][list_name] = []
            await self.update_group_settings(group_guid, settings)
            return True
        return False

    async def reset_locks(self, group_guid: str):
        """Reset all locks to default state"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        default_locks = DEFAULT_GROUP_SETTINGS["locks"]
        settings["locks"] = default_locks.copy()
        await self.update_group_settings(group_guid, settings)
        return True

    async def reset_restrictions(self, group_guid: str):
        """Reset all restrictions (blocks, mutes, etc)"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        settings["lists"]["blocked"] = []
        settings["lists"]["muted"] = []
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members SET warning = 0, mute = 0
                    WHERE group_guid = %s
                """, (group_guid,))
        
        await self.update_group_settings(group_guid, settings)
        return True

    async def add_custom_tag(self, group_guid: str, tag_name: str):
        """Add a custom tag to group"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        if "tags" not in settings["lists"]:
            settings["lists"]["tags"] = {}
        
        settings["lists"]["tags"][tag_name] = True
        await self.update_group_settings(group_guid, settings)
        return True

    async def get_all_tags(self, group_guid: str) -> Dict:
        """Get all tags for a group"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return {}
        return settings.get("lists", {}).get("tags", {})

    # ===== Group Member Methods =====
    async def add_user_to_group(self, group_guid: str, user_guid: str, user_rank: str = 'member', first_name: str = None, last_name: str = None, username: str = None):
        """Adds a user to a group's member list."""
        await self.add_user(user_guid)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO group_members (group_guid, user_guid, user_rank, first_name, last_name, username)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE first_name = VALUES(first_name), last_name = VALUES(last_name), username = VALUES(username)
                """, (group_guid, user_guid, user_rank, first_name, last_name, username))

    async def get_group_member(self, group_guid: str, user_guid: str) -> Optional[Dict]:
        """Retrieves a specific user's data for a specific group."""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
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
    
    async def get_user_display_name(self, group_guid: str, user_guid: str) -> str:
        """Get user's display name (first_name + last_name or username)"""
        member = await self.get_group_member(group_guid, user_guid)
        if not member:
            return user_guid
        
        name = ""
        if member.get("first_name"):
            name += member["first_name"]
        if member.get("last_name"):
            name += " " + member["last_name"]
        
        if not name.strip() and member.get("username"):
            name = member["username"]
        
        return name.strip() if name.strip() else user_guid
            
    async def decrement_all_muted_groups(self):
        """Decrease mute_group count by 1 for ALL groups where mute_group > 0."""
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
        """Decrease mute count by 1 for ALL users who are currently muted."""
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
        """Set mute count for a user in a specific group."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET mute = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (mute_count, group_guid, user_guid))

    async def get_group_total_messages(self, group_guid: str) -> int:
        """Get total messages for a group"""
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
        """Get total messages today for a group"""
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
        """Returns the number of muted members"""
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
        """Decrease mute count by 1"""
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
        """Check if user is currently muted"""
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
        """Get current mute count of a user in a group"""
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
        """Get all admins of a group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, user_rank, first_name, last_name, username
                    FROM group_members 
                    WHERE group_guid = %s AND user_rank = 'admin'
                """, (group_guid,))
                return list(await cursor.fetchall()) if await cursor.fetchall() else []

    async def get_group_admins_and_owner(self, group_guid: str) -> List[Dict]:
        """Get all admins and owner of a group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, user_rank, first_name, last_name, username
                    FROM group_members 
                    WHERE group_guid = %s AND user_rank IN ('admin', 'owner')
                """, (group_guid,))
                result = await cursor.fetchall()
                return list(result) if result else []

    async def get_group_owner_member(self, group_guid: str) -> Optional[Dict]:
        """Get owner member data"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, user_rank, first_name, last_name, username
                    FROM group_members 
                    WHERE group_guid = %s AND user_rank = 'owner'
                """, (group_guid,))
                return await cursor.fetchone()

    async def set_user_rank(self, group_guid: str, user_guid: str, rank: str) -> bool:
        """Set or update the rank of a user in a specific group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members 
                    SET user_rank = %s 
                    WHERE group_guid = %s AND user_guid = %s
                """, (rank, group_guid, user_guid))
                return cursor.rowcount > 0

    async def increment_user_message_count(self, group_guid: str, user_guid: str):
        """Increments total and daily message counts for a user in a group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET message_count = message_count + 1, messages_today = messages_today + 1
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
    
    async def increment_member_warning(self, group_guid: str, user_guid: str):
        """Increase user's warning count inside group_members table by +1"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET warning = warning + 1
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
    
    async def set_member_warning(self, group_guid: str, user_guid: str, count: int):
        """Set the user's warning count to an exact number"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE group_members
                    SET warning = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (count, group_guid, user_guid))

    async def reset_daily_messages(self):
        """Resets the daily message count for ALL users"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE group_members SET messages_today = 0")

    # User methods
    async def add_user(self, user_guid: str):
        """Add user (if not exists)"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
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
                return list(result) if result else []
    
    async def get_user(self, user_guid: str) -> Optional[Dict]:
        """Get user"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users WHERE user_guid = %s", (user_guid,))
                return await cursor.fetchone()

    # ===== Statistics Methods =====
    async def increment_report_stat(self, group_guid: str, stat_type: str):
        """Increment report statistics for a group"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return False
        
        if stat_type in settings.get("lists", {}).get("reports", {}):
            settings["lists"]["reports"][stat_type] += 1
            await self.update_group_settings(group_guid, settings)
            return True
        return False

    async def get_group_reports(self, group_guid: str) -> Dict:
        """Get all reports for a group"""
        settings = await self.get_group_settings(group_guid)
        if not settings:
            return {}
        return settings.get("lists", {}).get("reports", {})

    async def get_group_member_stats(self, group_guid: str, user_guid: str) -> Optional[Dict]:
        """Get statistics for a specific user in a group"""
        member = await self.get_group_member(group_guid, user_guid)
        if not member:
            return None
        
        settings = await self.get_group_settings(group_guid)
        lists = settings.get("lists", {}) if settings else {}
        
        return {
            "user_guid": member["user_guid"],
            "message_count": member["message_count"],
            "messages_today": member["messages_today"],
            "first_name": member.get("first_name", ""),
            "last_name": member.get("last_name", ""),
            "username": member.get("username", ""),
            "user_rank": member.get("user_rank", "member"),
            "is_exempt": user_guid in lists.get("exempt", []),
            "is_special": user_guid in lists.get("special", []),
            "is_blocked": user_guid in lists.get("blocked", []),
            "is_muted": user_guid in lists.get("muted", []),
            "is_admin": member.get("user_rank") == "admin",
            "is_owner": member.get("user_rank") == "owner"
        }

    async def get_top_group_members(self, group_guid: str, limit: int = 10) -> List[Dict]:
        """Get top members by message count"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, message_count, first_name, last_name, username
                    FROM group_members
                    WHERE group_guid = %s
                    ORDER BY message_count DESC
                    LIMIT %s
                """, (group_guid, limit))
                return await cursor.fetchall()

    # Forced Join Methods
    async def get_top3_active_members(self, group_guid: str):
        """Returns exactly 3 members by today's messages"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT user_guid, messages_today
                    FROM group_members
                    WHERE group_guid = %s
                    ORDER BY messages_today DESC
                """, (group_guid,))
                
                members = await cursor.fetchall()

                if not members:
                    return [
                        {"user_guid": "-", "messages_today": "-"},
                        {"user_guid": "-", "messages_today": "-"},
                        {"user_guid": "-", "messages_today": "-"}
                    ]

                grouped = {}
                for m in members:
                    grouped.setdefault(m["messages_today"], []).append(m)

                sorted_counts = sorted(grouped.keys(), reverse=True)

                top_members = []
                for count in sorted_counts:
                    users_with_same = grouped[count]
                    random.shuffle(users_with_same)
                    
                    for u in users_with_same:
                        if len(top_members) < 3:
                            top_members.append(u)
                        else:
                            break
                    if len(top_members) >= 3:
                        break

                while len(top_members) < 3:
                    top_members.append({
                        "user_guid": "-",
                        "messages_today": "-"
                    })

                return top_members

    async def add_forced_channel(self, channel_guid: str, channel_id: str):
        """Add a forced channel"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO forced_channels (channel_guid, channel_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE channel_id = VALUES(channel_id)
                """, (channel_guid, channel_id))

    async def get_all_forced_channels(self) -> List[Dict]:
        """Get all forced channels"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT channel_guid, channel_id FROM forced_channels")
                result = await cursor.fetchall()
                return list(result) if result else []
            
    async def get_all_groups(self) -> List[Dict]:
        """Get all groups"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT group_guid FROM `groups`")
                result = await cursor.fetchall()
                return list(result) if result else []

    async def get_pv_status(self) -> bool:
        """Get PV lock status"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT pv_locked FROM bot_settings WHERE id = 1")
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    async def set_pv_status(self, status: bool):
        """Set PV lock status"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO bot_settings (id, pv_locked) 
                    VALUES (1, %s) 
                    ON DUPLICATE KEY UPDATE pv_locked = VALUES(pv_locked)
                """, (int(status),))
                await conn.commit()

    async def set_group_capacity(self, capacity: int):
        """Set group capacity"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO bot_settings (id, max_groups) 
                    VALUES (1, %s) 
                    ON DUPLICATE KEY UPDATE max_groups = VALUES(max_groups)
                """, (capacity,))
                await conn.commit()
    
    async def get_group_capacity(self) -> int:
        """Get group capacity"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT max_groups FROM bot_settings WHERE id = 1")
                result = await cursor.fetchone()
                return int(result[0]) if result else 500

    async def remove_forced_channel_by_id(self, channel_id: str):
        """Remove a forced channel by ID"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM forced_channels WHERE channel_id = %s",
                    (channel_id,)
                )

    async def set_user_score_info(self, group_guid, user_guid, user_information=None, score=0):
        """Set user score information"""
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
        """Update user information"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE user_scores
                    SET user_information = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (json.dumps(user_information), group_guid, user_guid))
                await conn.commit()

    async def update_user_score(self, group_guid, user_guid, score):
        """Update user score"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE user_scores
                    SET score = %s
                    WHERE group_guid = %s AND user_guid = %s
                """, (score, group_guid, user_guid))
                await conn.commit()

    async def increment_user_score(self, group_guid, user_guid, delta=1):
        """Increment user score"""
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
        """Get user score info"""
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
        """Get all user scores"""
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
        """Returns exactly 3 members by score"""
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
                await cursor.execute("DELETE FROM scheduled_messages")
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

    # Rules methods
    async def set_group_rules(self, group_guid: str, rules_text: str):
        """Set or update rules for a group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO rules (group_guid, rules_text)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE 
                        rules_text = VALUES(rules_text),
                        updated_at = CURRENT_TIMESTAMP
                """, (group_guid, rules_text))

    async def get_group_rules(self, group_guid: str) -> Optional[str]:
        """Get rules for a specific group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT rules_text FROM rules WHERE group_guid = %s",
                    (group_guid,)
                )
                result = await cursor.fetchone()
                return result[0] if result and result[0] else None

    async def delete_group_rules(self, group_guid: str):
        """Delete rules for a group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM rules WHERE group_guid = %s",
                    (group_guid,)
                )

    # Welcome log methods
    async def add_welcome_log(self, group_guid: str, user_guid: str):
        """Add user to welcome log (to track if they're new)"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT IGNORE INTO welcome_logs (group_guid, user_guid)
                    VALUES (%s, %s)
                """, (group_guid, user_guid))

    async def is_user_new_to_group(self, group_guid: str, user_guid: str) -> bool:
        """Check if user is new to group"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT 1 FROM welcome_logs
                    WHERE group_guid = %s AND user_guid = %s
                """, (group_guid, user_guid))
                return not (await cursor.fetchone())
