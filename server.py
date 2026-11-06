# server.py — статический сервер для index.html / admin.html / view.html
# Язык: Python 3.11+ · Порт: из переменной PORT (по умолчанию 8000)
import os

from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.getenv("PORT", "8000"))


async def index(_request):
    return web.FileResponse(os.path.join(ROOT, "index.html"))


app = web.Application()
app.router.add_get("/", index)
app.router.add_static("/", path=ROOT, show_index=False)

if __name__ == "__main__":
    print(f"Сайт анкеты поднят: http://0.0.0.0:{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT, print=lambda *_: None)
