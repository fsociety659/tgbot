import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
DB_NAME = os.getenv("DB_NAME", "restaurant.db")

DB_URL = os.path.join(BASE_DIR, DB_NAME)

if not TOKEN:
    raise ValueError("❌ Ошибка: Переменная TOKEN не найдена! Проверь файл .env")

if not PROVIDER_TOKEN:
    raise ValueError(
        "❌ Ошибка: Переменная PROVIDER_TOKEN не найдена! Проверь файл .env"
    )
