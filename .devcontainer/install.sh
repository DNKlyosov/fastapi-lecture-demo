#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt

echo "Зависимости установлены. Сервер запустится автоматически при открытии Codespace."
