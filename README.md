# aiomost-tools

Async toolkit for building Mattermost bots.

`aiomost-tools` provides:

- an async Mattermost API client;
- event routing and dispatching;
- interactive button handling;
- FastAPI callback integration;
- websocket event listener;
- optional Redis-backed state storage.

- [Русский](#русский)
- [English](#english)

## Русский

### Установка

Базовая установка из GitHub:

```bash
pip install "aiomost-tools @ git+https://github.com/IliaPr/aiomost.git"
```

Базовая установка включает HTTP-клиент, роутеры, диспетчер, helpers для кнопок
и модели событий Mattermost.

Для обработки событий, кнопок и запуска FastAPI-приложения установи:

```bash
pip install "aiomost-tools[fastapi,websocket] @ git+https://github.com/IliaPr/aiomost.git"
```

Если нужны состояния пользователей в Redis:

```bash
pip install "aiomost-tools[fastapi,websocket,redis] @ git+https://github.com/IliaPr/aiomost.git"
```

Для установки всех опциональных интеграций:

```bash
pip install "aiomost-tools[all] @ git+https://github.com/IliaPr/aiomost.git"
```

### Опциональные зависимости

| Extra | Зависимости | Назначение |
| --- | --- | --- |
| `fastapi` | `fastapi`, `uvicorn` | HTTP endpoint для callback-ов Mattermost-кнопок. |
| `websocket` | `websockets` | Получение событий Mattermost в реальном времени. |
| `redis` | `redis` | Хранение пользовательских состояний. |
| `all` | Все extras | Полная установка. |

### Совместимость

| Компонент | Версии |
| --- | --- |
| Python | `>=3.10` |
| Mattermost API | HTTP API v4 |
| Mattermost websocket | `/api/v4/websocket` |
| httpx | `>=0.28.1,<0.29.0` |
| FastAPI | `>=0.139.0,<0.140.0` |
| Uvicorn | `>=0.30.0,<1.0.0` |
| websockets | `>=12.0,<16.0` |
| redis | `>=5.0.0,<7.0.0` |

### Отправка сообщения

```python
from aiomost import MMBot

bot = MMBot(
    api_url="https://mattermost.example.com",
    bot_token="MATTERMOST_BOT_TOKEN",
)

await bot.send_message(
    channel_id="CHANNEL_ID",
    text="Hello from aiomost",
)
```

### Обработка событий и кнопок

```python
from aiomost import MattermostBotApp

bot_app = MattermostBotApp(
    mattermost_url="https://mattermost.example.com",
    bot_token="MATTERMOST_BOT_TOKEN",
    public_base_url="https://bot.example.com",
)


@bot_app.message()
async def message(event, bot, app):
    post = event.data.post

    if post.message == "!ping":
        await bot.reply_message(
            channel_id=post.channel_id,
            message_id=post.id,
            text="pong",
            actions=app.actions([("ping_ok", "OK", "ping_ok")]),
        )


@bot_app.button("ping_ok")
async def ping_button(event):
    return {"update": {"message": "Button received"}}


app = bot_app.create_fastapi_app()
```

Запуск ASGI-приложения:

```bash
uvicorn your_module:app --host 0.0.0.0 --port 8000
```

`create_fastapi_app()` создаёт endpoints:

- `GET /health`
- `POST /mattermost/action`

Callback URL для интерактивных кнопок Mattermost:

```text
https://bot.example.com/mattermost/action
```

### Конфигурация через переменные окружения

```python
from aiomost import MattermostBotApp

bot_app = MattermostBotApp.from_env()
app = bot_app.create_fastapi_app()
```

Поддерживаемые переменные:

| Переменная | Обязательная | Описание |
| --- | --- | --- |
| `MATTERMOST_URL` | Да | Базовый URL Mattermost. |
| `MATTERMOST_BOT_TOKEN` | Да | Token бота. |
| `MATTERMOST_WS_URL` | Нет | Websocket URL. Если не задан, строится из `MATTERMOST_URL`. |
| `PUBLIC_BASE_URL` | Нет | Публичный URL приложения для callback-ов кнопок. |
| `REDIS_URL` | Нет | Redis URL для state storage. |

## English

### Installation

Base installation from GitHub:

```bash
pip install "aiomost-tools @ git+https://github.com/IliaPr/aiomost.git"
```

The base installation includes the HTTP client, routers, dispatcher, button
helpers, and Mattermost event models.

For event handling, interactive buttons, and FastAPI app integration:

```bash
pip install "aiomost-tools[fastapi,websocket] @ git+https://github.com/IliaPr/aiomost.git"
```

If you need Redis-backed user state:

```bash
pip install "aiomost-tools[fastapi,websocket,redis] @ git+https://github.com/IliaPr/aiomost.git"
```

To install every optional integration:

```bash
pip install "aiomost-tools[all] @ git+https://github.com/IliaPr/aiomost.git"
```


### Optional Dependencies

| Extra | Dependencies | Purpose |
| --- | --- | --- |
| `fastapi` | `fastapi`, `uvicorn` | HTTP endpoint for Mattermost button callbacks. |
| `websocket` | `websockets` | Real-time Mattermost event stream. |
| `redis` | `redis` | User state storage. |
| `all` | All extras | Full installation. |

### Compatibility

| Component | Versions |
| --- | --- |
| Python | `>=3.10` |
| Mattermost API | HTTP API v4 |
| Mattermost websocket | `/api/v4/websocket` |
| httpx | `>=0.28.1,<0.29.0` |
| FastAPI | `>=0.139.0,<0.140.0` |
| Uvicorn | `>=0.30.0,<1.0.0` |
| websockets | `>=12.0,<16.0` |
| redis | `>=5.0.0,<7.0.0` |

### Send a Message

```python
from aiomost import MMBot

bot = MMBot(
    api_url="https://mattermost.example.com",
    bot_token="MATTERMOST_BOT_TOKEN",
)

await bot.send_message(
    channel_id="CHANNEL_ID",
    text="Hello from aiomost",
)
```

### Event And Button Handling

```python
from aiomost import MattermostBotApp

bot_app = MattermostBotApp(
    mattermost_url="https://mattermost.example.com",
    bot_token="MATTERMOST_BOT_TOKEN",
    public_base_url="https://bot.example.com",
)


@bot_app.message()
async def message(event, bot, app):
    post = event.data.post

    if post.message == "!ping":
        await bot.reply_message(
            channel_id=post.channel_id,
            message_id=post.id,
            text="pong",
            actions=app.actions([("ping_ok", "OK", "ping_ok")]),
        )


@bot_app.button("ping_ok")
async def ping_button(event):
    return {"update": {"message": "Button received"}}


app = bot_app.create_fastapi_app()
```

Run the ASGI app:

```bash
uvicorn your_module:app --host 0.0.0.0 --port 8000
```

`create_fastapi_app()` creates:

- `GET /health`
- `POST /mattermost/action`

Mattermost interactive button callback URL:

```text
https://bot.example.com/mattermost/action
```

### Environment Configuration

```python
from aiomost import MattermostBotApp

bot_app = MattermostBotApp.from_env()
app = bot_app.create_fastapi_app()
```

Supported variables:

| Variable | Required | Description |
| --- | --- | --- |
| `MATTERMOST_URL` | Yes | Mattermost base URL. |
| `MATTERMOST_BOT_TOKEN` | Yes | Bot token. |
| `MATTERMOST_WS_URL` | No | Websocket URL. If omitted, it is built from `MATTERMOST_URL`. |
| `PUBLIC_BASE_URL` | No | Public application URL for button callbacks. |
| `REDIS_URL` | No | Redis URL for state storage. |

