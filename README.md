# fastapi-lecture-demo

Учебный HTTP API для демонстрации создания, чтения, изменения и удаления ресурсов на FastAPI.

[![Открыть в GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/DNKlyosov/fastapi-lecture-demo?quickstart=1)

## Быстрый запуск в браузере

1. Откройте репозиторий в GitHub Codespaces. Конфигурация `.devcontainer` установит зависимости и запустит Uvicorn на порту 8000.
2. Перейдите по ссылке порта **8000** во вкладке **Ports**.
3. По корневому адресу откроется **таблица устройств**. В таблице есть все ID, на них можно нажимать.
4. Для HTTP-методов и проверки тела запросов откройте **`/docs`** (ссылка в верхнем правом углу каталога).

## Операции

| Метод | Путь | Назначение | Типичный статус |
|---|---|---|---|
| GET | `/api/products` | Список, `type` и `limit` | 200 |
| GET | `/api/products/{product_id}` | Устройство по ID | 200 / 404 |
| POST | `/api/products` | Создать устройство | 201 / 409 / 422 |
| PUT | `/api/products/{product_id}` | Полностью заменить данные существующего устройства | 200 / 404 |
| PATCH | `/api/products/{product_id}` | Частично изменить поля | 200 / 404 / 422 |
| DELETE | `/api/products/{product_id}` | Удалить устройство | 204 / 404 |
| POST | `/api/reset` | Восстановить исходные 5 устройств | 200 |

`/docs` — интерактивная документация Swagger UI; `/openapi.json` — спецификация OpenAPI.

**Начальный каталог:** 5 устройств с ID 1–5. Первый POST создаёт устройство ID 6, последующий GET `/api/products/6` его возвращает.

### Пример JSON для POST /api/products

```json
{
  "name": "CO2 Sensor",
  "type": "sensor",
  "status": "active",
  "price": 35.5,
  "tags": ["climate", "indoor"]
}
```

Ответ содержит новый `id`, HTTP-статус `201 Created` и заголовок `Location: /api/products/6`.

### Пример JSON для PATCH /api/products/6

```json
{
  "price": 39.9,
  "status": "inactive"
}
```

Повторный GET должен вернуть изменённые значения.

## Что изменилось относительно первой версии

- Добавлена главная HTML-страница с таблицей устройств и ссылками на JSON каждого ID.
- Добавлены POST, PUT, PATCH и DELETE в Swagger UI.
- Добавлены фильтрация `GET /api/products?type=sensor` и ограничение `?limit=2`.
- Добавлен `POST /api/reset` для восстановления исходных данных во время лекции.
- Сохранены автозапуск через Codespaces и автоматические проверки.

## Установка и запуск локально

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Для запуска внутри Codespaces достаточно:

```bash
bash .devcontainer/start.sh
```

Для остановки фонового сервера:

```bash
pkill -f '[u]vicorn app.main:app'
```

Проверка:

```bash
.venv/bin/python -m pytest -q
```

## Важно

Это **учебный сервер**, не готовый сервис для публикации в интернете. Данные находятся в памяти одного процесса и сбрасываются после перезапуска или через `/api/reset`. При одновременной работе нескольких пользователей используется общий каталог. В приложении нет аутентификации; не делайте порт публичным без необходимости.
