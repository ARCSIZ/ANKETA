# bot.py — приветствие в ЛС + кнопка входа в анкету (Mini App)
# Требования: Python 3.11+, пакеты из requirements.txt
# Переменные окружения: BOT_TOKEN, WEBAPP_URL (см. .env.example)
import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000/")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Создай .env по образцу .env.example")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(m: Message):
    """Приветствие + inline-кнопка, открывающая анкету как Mini App."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Открыть анкету",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ]]
    )
    await m.answer(
        f"Привет, {m.from_user.first_name or 'игрок'}!\n"
        "Это набор в команду майнкрафт-сервера.\n"
        "Жми кнопку ниже: выбери вакансию и пройди короткий тест — "
        "результат сразу прилетит администратору.",
        reply_markup=kb,
    )


@dp.message()
async def fallback(m: Message):
    """Любое другое сообщение — мягко возвращаем к анкете."""
    await m.answer("Чтобы подать заявку, напиши /start и нажми кнопку анкеты.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Craft Team bot запущен (polling). Ctrl+C — остановить.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
