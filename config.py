import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "ISI_TOKEN_BOT_KAMU")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "ISI_GROQ_API_KEY_KAMU")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

DB_NAME = "keuangan.db"
