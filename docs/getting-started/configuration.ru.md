# Конфигурация FastAPI-приложения

`MattermostBotApp` умеет читать настройки из окружения. Для FastAPI-приложения
это основной способ конфигурации: код остаётся одинаковым во всех окружениях,
а адреса и секреты передаются при запуске.

## Переменные окружения

Создайте локальный файл `.env`:

```dotenv title=".env"
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_BOT_TOKEN=your-token
PUBLIC_BASE_URL=https://bot.example.com
```

Две переменные обязательны:

| Переменная | Назначение |
| --- | --- |
| `MATTERMOST_URL` | Базовый HTTP(S)-адрес Mattermost |
| `MATTERMOST_BOT_TOKEN` | Токен бота Mattermost |

`PUBLIC_BASE_URL` нужен, если приложение отправляет интерактивные кнопки. Это
публичный адрес FastAPI-приложения без пути callback-а.


## Создание приложения

Настройки загружаются методом `from_env()`:

```python title="app.py"
from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()
app = bot_app.create_fastapi_app()
```

`app` — обычное ASGI-приложение FastAPI. При старте оно подключается к
Mattermost WebSocket, а при остановке корректно завершает фоновую задачу.
Обработчики событий можно размещать между созданием `bot_app` и `app`.

## Локальный запуск

Сама библиотека не читает `.env`-файл. Сначала загрузите переменные в окружение,
затем запустите Uvicorn:

=== "Linux и macOS"

    ```bash
    set -a
    source .env
    set +a
    uvicorn app:app --reload
    ```

=== "Без .env-файла"

    ```bash
    MATTERMOST_URL="https://mattermost.example.com" \
    MATTERMOST_BOT_TOKEN="your-token" \
    PUBLIC_BASE_URL="https://bot.example.com" \
    uvicorn app:app --reload
    ```

После запуска доступны служебные endpoints:

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/health` | Проверка доступности приложения |
| `POST` | `/mattermost/action` | Callback интерактивных кнопок |

Для callback-ов значение `PUBLIC_BASE_URL` должно быть доступно серверу
Mattermost. Адрес `127.0.0.1` подходит для healthcheck, но не для кнопок.

Проверить приложение можно командой:

```bash
curl http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status": "ok"}
```

## Дополнительные интеграции

Если используются состояния, добавьте Redis:

```dotenv title=".env"
REDIS_URL=redis://localhost:6379/0
```

WebSocket URL строится автоматически из `MATTERMOST_URL`. Переопределять его
нужно только при нестандартной сетевой конфигурации:

```dotenv title=".env"
MATTERMOST_WS_URL=wss://mattermost.example.com/api/v4/websocket
```

Итоговый набор поддерживаемых настроек:

| Переменная | Обязательная | Назначение |
| --- | :---: | --- |
| `MATTERMOST_URL` | Да | Адрес Mattermost |
| `MATTERMOST_BOT_TOKEN` | Да | Токен бота |
| `PUBLIC_BASE_URL` | Нет | Публичный адрес FastAPI-приложения |
| `REDIS_URL` | Нет | Подключение к Redis |
| `MATTERMOST_WS_URL` | Нет | Пользовательский WebSocket URL |
