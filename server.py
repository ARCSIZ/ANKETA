# server.py — алиас для обратной совместимости: запускает тот же main.py
# Реальная точка входа проекта — main.py (см. bothost.json)
import asyncio

from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
