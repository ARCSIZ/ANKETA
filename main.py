# main.py — точка входа для Bothost: веб-сервер + Telegram-бот в ОДНОМ процессе
#
# Требования Bothost к веб-сервисам, которые здесь выполнены:
#   - контейнер слушает 0.0.0.0, порт берётся из переменной PORT
#     (и должен совпадать с полем «Порт» в панели Bothost)
#   - GET /health — проверка живости сервиса
#
# Дополнительно:
#   - GET /api/env.js — отдаёт страницам window.__ENV__ с ADMIN_ID/BOT_TOKEN
#     из переменных окружения хостинга (.env на Bothost НЕ читается автоматом)
#   - в том же процессе поднимается long polling бота из bot.py
import asyncio
import json
import os

from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.getenv("PORT", "8000"))
ADMIN_ID = os.getenv("ADMIN_ID", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def index(_request):
    return web.FileResponse(os.path.join(ROOT, "index.html"))


async def health(_request):
    # Bothost дёргает этот эндпоинт, чтобы понять, что контейнер жив
    return web.json_response({"ok": True, "service": "craft-team"})


async def env_js(_request):
    # Страницы читают конфиг отсюда: window.__ENV__ имеет приоритет №1
    payload = {"ADMIN_ID": ADMIN_ID, "BOT_TOKEN": BOT_TOKEN}
    body = "window.__ENV__ = " + json.dumps(payload, ensure_ascii=False) + ";"
    return web.Response(text=body, content_type="application/javascript")


def build_app():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/api/env.js", env_js)
    app.router.add_static("/", path=ROOT, show_index=False)
    return app


async def main():
    runner = web.AppRunner(build_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    print(f"[web] сайт + /health подняты на http://0.0.0.0:{PORT}")

    try:
        from bot import run_bot, bot as bot_instance
        if bot_instance is not None:
            await run_bot()  # блокирует до остановки процесса
        else:
            print("[web] BOT_TOKEN не задан — работает только сайт (демо-режим).")
            await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Остановлено.")
