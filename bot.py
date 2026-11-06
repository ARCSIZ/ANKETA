# bot.py — приветствие в ЛС + кнопка входа в анкету (Mini App)
#
# Можно запускать отдельно:  python bot.py
# На Bothost бота поднимает main.py в том же процессе, что и сайт.
#
# Переменные окружения: BOT_TOKEN, ADMIN_ID, WEBAPP_URL (см. .env.example)
import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    MenuButtonWebApp,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Bothost: после включения «Использовать домен» впиши сюда выданный https://<id>.bothost.tech
WEBAPP_URL = (
    os.getenv("WEBAPP_URL") or os.getenv("PUBLIC_URL") or "http://localhost:3594/"
).rstrip("/") + "/"

bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
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


@dp.message(Command("id"))
async def chat_id(m: Message):
    """/id в группе стаффа — покажет её ID для переменной STAFF_CHAT_ID."""
    kind = "группа" if m.chat.type in ("group", "supergroup") else "личный чат"
    await m.answer(
        f"Тип: {kind}\nID чата: <code>{m.chat.id}</code>\n\n"
        "Впиши это значение в переменную <b>STAFF_CHAT_ID</b> в панели Bothost "
        "и дай боту право «Пригласительные ссылки».",
        parse_mode="HTML",
    )


@dp.message(F.chat.type == "private")
async def fallback(m: Message):
    """Личка: любое другое сообщение — мягко возвращаем к анкете."""
    await m.answer("Чтобы подать заявку, напиши /start и нажми кнопку анкеты.")


async def run_bot():
    """Long polling + кнопка меню чата. Вызывается из main.py или напрямую."""
    if bot is None:
        raise RuntimeError("BOT_TOKEN не задан. Создай .env по образцу .env.example")
    try:
        # Вешаем «Анкета» на меню чата — BotFather настраивать не обязательно
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Анкета", web_app=WebAppInfo(url=WEBAPP_URL))
        )
    except Exception as e:
        print(f"[bot] setChatMenuButton не удался: {e}")
    await bot.delete_webhook(drop_pending_updates=True)
    print(f"[bot] polling запущен, анкета: {WEBAPP_URL}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
