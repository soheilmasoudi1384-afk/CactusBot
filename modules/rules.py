"""
Rules Management Module
مدیریت قوانین گروه‌ها برای Rubika
"""
from core import db
from typing import Optional

class RulesManager:
    
    @staticmethod
    async def set_rules(group_guid: str, rules_text: str) -> bool:
        """
        تنظیم قوانین گروه
        
        Parameters:
            group_guid (str): شناسه گروه
            rules_text (str): متن قوانین
            
        Returns:
            bool: موفقیت عملیات
        """
        try:
            await db.set_group_rules(group_guid, rules_text)
            return True
        except Exception as e:
            print(f"Error setting rules: {e}")
            return False
    
    @staticmethod
    async def get_rules(group_guid: str) -> Optional[str]:
        """
        دریافت قوانین گروه
        
        Parameters:
            group_guid (str): شناسه گروه
            
        Returns:
            Optional[str]: متن قوانین یا None
        """
        try:
            return await db.get_group_rules(group_guid)
        except Exception as e:
            print(f"Error getting rules: {e}")
            return None
    
    @staticmethod
    async def delete_rules(group_guid: str) -> bool:
        """
        حذف قوانین گروه
        
        Parameters:
            group_guid (str): شناسه گروه
            
        Returns:
            bool: موفقیت عملیات
        """
        try:
            await db.delete_group_rules(group_guid)
            return True
        except Exception as e:
            print(f"Error deleting rules: {e}")
            return False
