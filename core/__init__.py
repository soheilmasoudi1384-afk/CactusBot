from core.database import Database
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT  # فرضی، طبق config خودت تنظیم کن

db = Database(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=DB_PORT,
)
