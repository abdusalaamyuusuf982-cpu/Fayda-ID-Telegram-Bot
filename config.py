import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram Payment Provider Token (e.g. Stripe, or Telegram Stars XTR)
# Leave empty if you don't have one setup yet, but payments will fail
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")

# Database Config - defaults to local SQLite for easy development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

ADMIN_ID = os.getenv("ADMIN_ID", "2146240208")
