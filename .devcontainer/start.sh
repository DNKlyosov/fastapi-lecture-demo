#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  echo "Виртуальное окружение отсутствует — устанавливаю зависимости."
  bash .devcontainer/install.sh
fi

if curl -fsS --max-time 2 http://127.0.0.1:8000/openapi.json >/dev/null 2>&1; then
  echo "FastAPI уже работает на порту 8000."
  exit 0
fi

nohup .venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  > /tmp/fastapi-lecture-demo.log 2>&1 < /dev/null &

echo "Запуск FastAPI. Откройте Ports → 8000 → Open in Browser (перенаправит на /docs)."
echo "Лог: /tmp/fastapi-lecture-demo.log"
