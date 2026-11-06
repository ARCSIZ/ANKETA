# main.py — точка входа для Bothost: веб-сервер + Telegram-бот в ОДНОМ процессе
#
# Хранилище общее для всех пользователей: data/store.json на сервере.
# Токен бота НЕ уходит в браузер — все уведомления шлёт сервер.
import asyncio
import json
import os
import time

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.getenv("PORT", "3594"))
ADMIN_ID = str(os.getenv("ADMIN_ID", "")).strip()
BOT_TOKEN = str(os.getenv("BOT_TOKEN", "")).strip()

DATA_DIR = os.path.join(ROOT, "data")
STORE = os.path.join(DATA_DIR, "store.json")
_lock = asyncio.Lock()

DEFAULT_ROLES = [
    {
        "id": "r1", "name": "Хелпер", "icon": "i-pick", "color": "#7fdb4f", "open": True,
        "desc": "Правая рука игроков: отвечает в чате, помогает новичкам освоиться и следит за настроением сервера.",
        "questions": [
            {"id": "q1", "type": "text", "text": "Твой ник в Minecraft и возраст?"},
            {"id": "q2", "type": "long", "text": "Расскажи о своём опыте помощи или модерации на других серверах.", "min": 24},
            {"id": "q3", "type": "choice", "text": "Игрок в чате просит выдать ему вещи «по-быстрому». Твои действия?",
             "options": ["Выдам, если он играет давно", "Вежливо откажу и объясню правила", "Проигнорирую", "Сразу накажу мутом"]},
            {"id": "q4", "type": "multi", "text": "Что готов(а) делать на сервере?",
             "options": ["Отвечать в чате", "Помогать новичкам", "Следить за порядком", "Придумывать ивенты"]},
        ],
    },
    {
        "id": "r2", "name": "Модератор", "icon": "i-sword", "color": "#f0503c", "open": True,
        "desc": "Страж порядка: разбирает репорты, ловит читеров и решает конфликты быстро и честно.",
        "questions": [
            {"id": "q1", "type": "text", "text": "Твой ник в Minecraft и возраст?"},
            {"id": "q2", "type": "long", "text": "Опиши конфликтную ситуацию, которую ты разрешил(а), и чем всё закончилось.", "min": 24},
            {"id": "q3", "type": "choice", "text": "Заметил(а) подозрительного игрока с читами. Первым делом:",
             "options": ["Сниму доказательства и доложу старшим", "Сразу забаню", "Спрошу в общем чате", "Напишу ему в личку"]},
            {"id": "q4", "type": "text", "text": "Сколько часов в неделю готов(а) уделять серверу?"},
        ],
    },
    {
        "id": "r3", "name": "Билдер", "icon": "i-block", "color": "#f6c453", "open": True,
        "desc": "Архитектор мира: спавны, хабы, арены и декор — всё, что делает сервер красивым.",
        "questions": [
            {"id": "q1", "type": "text", "text": "Твой ник в Minecraft и возраст?"},
            {"id": "q2", "type": "long", "text": "Опиши свой стиль и лучшие постройки. Можно ссылки на скриншоты.", "min": 24},
            {"id": "q3", "type": "choice", "text": "В каком стиле строишь чаще всего?",
             "options": ["Средневековье", "Модерн", "Фэнтези", "Органика / терраформинг"]},
        ],
    },
    {
        "id": "r4", "name": "Ивент-менеджер", "icon": "i-star", "color": "#59e0e6", "open": True,
        "desc": "Душа вечеринки: придумывает ивенты, пишет сценарии и превращает вечер пятницы в приключение.",
        "questions": [
            {"id": "q1", "type": "text", "text": "Твой ник в Minecraft и возраст?"},
            {"id": "q2", "type": "long", "text": "Придумай мини-ивент на 30 минут и опиши его сценарий по шагам.", "min": 24},
            {"id": "q3", "type": "multi", "text": "Что умеешь?",
             "options": ["Писать сценарии", "Строить арены", "Вести трансляции", "Монтировать видео"]},
        ],
    },
]


def read_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(STORE):
        data = {"roles": DEFAULT_ROLES, "subs": []}
        with open(STORE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    try:
        with open(STORE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data.setdefault("roles", DEFAULT_ROLES)
    data.setdefault("subs", [])
    return data


def write_store(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STORE)


def is_admin(request):
    key = request.query.get("key") or request.headers.get("X-Admin-Key") or ""
    return bool(ADMIN_ID) and str(key).strip() == ADMIN_ID


async def tg(method, payload):
    """Отправка через Bot API с сервера — токен не покидает хостинг."""
    if not BOT_TOKEN:
        return {"ok": False, "description": "BOT_TOKEN не задан"}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as r:
                return await r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


# ---------------------------------------------------------------- API
async def api_roles(request):
    return web.json_response(read_store()["roles"])


async def api_roles_save(request):
    if not is_admin(request):
        return web.json_response({"ok": False, "error": "forbidden"}, status=403)
    roles = await request.json()
    async with _lock:
        data = read_store()
        data["roles"] = roles
        write_store(data)
    return web.json_response({"ok": True, "count": len(roles)})


async def api_subs(request):
    if not is_admin(request):
        return web.json_response({"ok": False, "error": "forbidden"}, status=403)
    return web.json_response(read_store()["subs"])


async def api_submit(request):
    """Приём анкеты: сохраняем + уведомляем админа в ЛС."""
    sub = await request.json()
    sub["id"] = int(time.time() * 1000)
    sub["ts"] = sub["id"]
    sub["status"] = "new"
    photos = sub.pop("photos", []) or []
    sub["photoCount"] = len(photos)

    async with _lock:
        data = read_store()
        data["subs"].insert(0, sub)
        data["subs"] = data["subs"][:500]
        write_store(data)

    def esc(t):
        return str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = "\n\n".join(
        f"{i + 1}. {esc(a.get('q'))}\n   → {esc(a.get('a'))}"
        for i, a in enumerate(sub.get("answers", []))
    )
    text = (
        "<b>НОВАЯ ЗАЯВКА НА СЕРВЕР</b>\n\n"
        f"Игрок: {esc(sub.get('userName'))}"
        + (f" (@{esc(sub.get('username'))})" if sub.get("username") else "")
        + f"\nID: <code>{esc(sub.get('userId'))}</code>\n"
        f"Вакансия: <b>{esc(sub.get('roleName'))}</b>\n"
        f"Время: {esc(sub.get('dateStr'))}\n"
        f"Скриншотов: {len(photos)}\n\n{lines}"
    )
    res = await tg("sendMessage", {"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"})

    for i, p in enumerate(photos[:3]):
        await tg("sendPhoto", {
            "chat_id": ADMIN_ID,
            "photo": p if str(p).startswith("http") else None,
            "caption": f"{sub.get('userName')} · {sub.get('roleName')} · фото {i + 1}/{len(photos)}",
        }) if str(p).startswith("http") else None

    return web.json_response({"ok": True, "delivered": bool(res.get("ok")), "id": sub["id"]})


async def api_sub_update(request):
    if not is_admin(request):
        return web.json_response({"ok": False, "error": "forbidden"}, status=403)
    body = await request.json()
    sid = int(request.match_info["sid"])
    action = body.get("action")
    notify = bool(body.get("notify"))

    async with _lock:
        data = read_store()
        target = next((s for s in data["subs"] if int(s.get("id", 0)) == sid), None)
        if action == "delete":
            data["subs"] = [s for s in data["subs"] if int(s.get("id", 0)) != sid]
        elif target:
            target["status"] = action
        write_store(data)

    delivered = False
    if notify and target and action in ("accepted", "rejected") and target.get("userId"):
        txt = (
            f"<b>CRAFT TEAM</b>\nТвоя заявка на вакансию «{target.get('roleName')}» — <b>принята</b>. "
            "Администратор скоро напишет тебе лично. Добро пожаловать в команду!"
            if action == "accepted" else
            f"<b>CRAFT TEAM</b>\nЗаявка на вакансию «{target.get('roleName')}» отклонена. "
            "Не расстраивайся — набери опыта и попробуй снова позже."
        )
        r = await tg("sendMessage", {"chat_id": target["userId"], "text": txt, "parse_mode": "HTML"})
        delivered = bool(r.get("ok"))

    return web.json_response({"ok": True, "delivered": delivered})


async def api_test(request):
    if not is_admin(request):
        return web.json_response({"ok": False, "error": "forbidden"}, status=403)
    r = await tg("sendMessage", {
        "chat_id": ADMIN_ID,
        "text": "<b>CRAFT TEAM</b>\nТестовое сообщение: связь панели с ботом работает.",
        "parse_mode": "HTML",
    })
    return web.json_response(r)


# ------------------------------------------------------------- страницы
async def index(_r):
    return web.FileResponse(os.path.join(ROOT, "index.html"))


async def health(_r):
    return web.json_response({"ok": True, "service": "craft-team"})


async def env_js(_r):
    # В браузер уходит ТОЛЬКО admin_id — токен остаётся на сервере
    body = "window.__ENV__ = " + json.dumps({"ADMIN_ID": ADMIN_ID}, ensure_ascii=False) + ";"
    return web.Response(text=body, content_type="application/javascript")


def build_app():
    app = web.Application(client_max_size=24 * 1024 * 1024)
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/api/env.js", env_js)
    app.router.add_get("/api/roles", api_roles)
    app.router.add_post("/api/roles", api_roles_save)
    app.router.add_get("/api/subs", api_subs)
    app.router.add_post("/api/submit", api_submit)
    app.router.add_post("/api/subs/{sid}", api_sub_update)
    app.router.add_post("/api/test", api_test)
    app.router.add_static("/", path=ROOT, show_index=False)
    return app


async def main():
    read_store()
    runner = web.AppRunner(build_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    print(f"[web] сайт поднят на http://0.0.0.0:{PORT}")

    try:
        from bot import run_bot, bot as bot_instance
        if bot_instance is not None:
            await run_bot()
        else:
            print("[web] BOT_TOKEN не задан — работает только сайт.")
            await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Остановлено.")
