#!/usr/bin/env bash
pip install -r requirements.txt

# Запуск Uvicorn
# --host 0.0.0.0 позволяет принимать запросы извне
# --port $PORT использует динамический порт, который предоставит Render
uvicorn web_server:app --host 0.0.0.0 --port $PORT
