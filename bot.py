# bot.py — приветствие в ЛС + кнопка входа в анкету (Mini App)
#
# Бот отвечает ТОЛЬКО в личных сообщениях.
# В группах он молчит: единственное исключение — команда /id,
# и та отвечает лишь администратору (ADMIN_ID), чтобы можно было
# узнать STAFF_CHAT_ID при настройке.
#
# Можно запускать отдельно:  python bot.py
# На Bothost бота поднимает main.py в том же процессе, что и сайт.
#
# Переменные окружения: BOT_TOKEN, ADMIN_ID, WEBAPP_URL, STAFF_CHAT_ID
import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    MenuButtonWebApp,
    BotCommand,
    BotCommandScopeAllPrivateChats,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = str(os.getenv("ADMIN_ID", "")).strip()
# Bothost: после включения «Использовать домен» впиши сюда выданный https://<id>.bothost.tech
WEBAPP_URL = (
    os.getenv("WEBAPP_URL") or os.getenv("PUBLIC_URL") or "http://localhost:3594/"
).rstrip("/") + "/"

bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

# ── роутер лички: сюда попадают только приватные чаты ──────────────────
private = Router()
private.message.filter(F.chat.type == ChatType.PRIVATE)

# ── роутер групп: всё, что не личка ────────────────────────────────────
groups = Router()
groups.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))


@private.message(CommandStart())
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


@private.message(Command("id"))
async def my_id(m: Message):
    """В личке показывает твой user id (пригодится для ADMIN_ID)."""
    await m.answer(f"Твой ID: <code>{m.from_user.id}</code>", parse_mode="HTML")


@private.message()
async def fallback(m: Message):
    """Личка: любое другое сообщение — мягко возвращаем к анкете."""
    await m.answer("Чтобы подать заявку, напиши /start и нажми кнопку анкеты.")


@groups.message(Command("id"))
async def chat_id(m: Message):
    """Единственный ответ бота в группе — и только администратору."""
    if not ADMIN_ID or str(m.from_user.id) != ADMIN_ID:
        return  # для всех остальных бот молчит
    await m.answer(
        f"ID чата: <code>{m.chat.id}</code>\n\n"
        "Впиши это значение в переменную <b>STAFF_CHAT_ID</b> в панели Bothost "
        "и дай боту право «Пригласительные ссылки».",
        parse_mode="HTML",
    )


# Любые другие сообщения в группах молча игнорируются:
# хендлеров под них просто нет, а роутер лички до групп не достаёт.
dp.include_router(private)
dp.include_router(groups)


async def run_bot():
    """Long polling + кнопка меню чата. Вызывается из main.py или напрямую."""
    if bot is None:
        raise RuntimeError("BOT_TOKEN не задан. Создай .env по образцу .env.example")
    try:
        # Кнопка «Анкета» в меню чата — только для личных чатов
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Анкета", web_app=WebAppInfo(url=WEBAPP_URL))
        )
        # Команды показываем тоже только в личке, чтобы не мусорить в группах
        await bot.set_my_commands(
            [BotCommand(command="start", description="Открыть анкету")],
            scope=BotCommandScopeAllPrivateChats(),
        )
    except Exception as e:
        print(f"[bot] настройка меню не удалась: {e}")
    await bot.delete_webhook(drop_pending_updates=True)
    print(f"[bot] polling запущен (отвечает только в ЛС), анкета: {WEBAPP_URL}")
    # Забираем только нужные типы апдейтов — меньше лишнего трафика из групп
    await dp.start_polling(bot, allowed_updates=["message"])


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
