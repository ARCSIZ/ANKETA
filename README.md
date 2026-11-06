# CRAFT TEAM — набор в состав Minecraft-сервера

Анкета-тест как Telegram Mini App: игрок выбирает вакансию, проходит тест,
результат мгновенно приходит администратору в ЛС от бота и сохраняется в
реестр заявок.

## Стек

- **Язык:** Python **3.11+** (рекомендовано 3.12, см. `runtime.txt`)
- **Веб-сервер:** `aiohttp` — слушает порт **`8000`** (переопределяется переменной `PORT`)
- **Бот:** `aiogram 3` (long polling, webhook не нужен)
- **Фронт:** статические `index.html` / `admin.html` / `view.html` (Tailwind CDN)

## Файлы

| Файл            | Назначение                                              |
|-----------------|---------------------------------------------------------|
| `index.html`    | Mini App: выбор вакансии и прохождение теста            |
| `admin.html`    | Панель админа: редактор вакансий/вопросов, ENV, данные  |
| `view.html`     | Реестр заявок: просмотр ответов, принять/отклонить      |
| `bot.py`        | Бот: приветствие в ЛС + кнопка открытия анкеты          |
| `server.py`     | Раздаёт статику на порту 8000                           |
| `requirements.txt` / `.env.example` / `Procfile` / `runtime.txt` | Деплой |

## Быстрый старт локально

```bash
pip install -r requirements.txt
cp .env.example .env   # впиши BOT_TOKEN, ADMIN_ID, WEBAPP_URL
python server.py       # сайт: http://localhost:8000
python bot.py          # бот (вторым процессом)
```

## Переменные окружения

| Переменная   | Описание                                             |
|--------------|------------------------------------------------------|
| `BOT_TOKEN`  | Токен бота от @BotFather                             |
| `ADMIN_ID`   | Твой числовой Telegram ID (@userinfobot)             |
| `WEBAPP_URL` | Публичный HTTPS-адрес сайта (для кнопки Mini App)    |
| `PORT`       | Порт веб-сервера, по умолчанию `8000`                |

Те же `ADMIN_ID` / `BOT_TOKEN` один раз вводятся в `admin.html` → вкладка
«Бот и данные» — страницы читают их из localStorage домена.

## Деплой на хостинг (Railway / Render / Heroku-совместимые)

1. Залей репозиторий. Хостинг подхватит `Procfile`:
   - `web` → `python server.py` (порт берётся из `PORT` автоматически)
   - `worker` → `python bot.py`
2. Добавь переменные `BOT_TOKEN`, `ADMIN_ID`, `WEBAPP_URL` в панели хостинга.
3. У BotFather выполни `/setmenubutton` (или `/newapp`) со ссылкой `WEBAPP_URL` —
   анкета будет открываться прямо в Telegram.

> Mini App требует публичный HTTPS — на Railway/Render сертификат выдаётся
> автоматически.
