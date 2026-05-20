import os
from dotenv import load_dotenv

load_dotenv()

# Bot config
BOT_TOKEN = os.getenv("BOT_TOKEN", "BCAGEF0LLPYGTCVLJBPEYEICYZYOEUYKLTBOLQAUDXHGWVXGZZPTVRAFVAWGVOZV")

# MySQL config
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "rubika_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "NewStrongPassword123!")
DB_NAME = os.getenv("DB_NAME", "cactusbo_rubika")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

# Admin config
ADMIN_GUIDS = os.getenv("ADMIN_GUIDS", "").split("b0FO6Vu07lD0e5d51ee47c60478bc661")

print("Config loaded successfully")

