# aiomost-tools

Асинхронный Python-инструментарий для создания Mattermost-ботов.

[Установить](getting-started/installation.md){ .md-button .md-button--primary }
[GitHub](https://github.com/IliaPr/aiomost){ .md-button }

## Возможности

- асинхронный клиент Mattermost HTTP API v4;
- маршрутизация событий и фильтры обработчиков;
- интерактивные кнопки и callback-и;
- получение событий через WebSocket;
- интеграция с FastAPI;
- хранение состояний пользователей в Redis.

## Быстрый старт

```python title="bot.py"
from aiomost import MattermostBotApp


bot_app = MattermostBotApp(
    mattermost_url="https://mattermost.example.com",
    bot_token="MATTERMOST_BOT_TOKEN",
    public_base_url="https://bot.example.com",
)


@bot_app.message()
async def handle_message(event, bot):
    post = event.data.post

    if post.message == "!ping":
        await bot.reply_message(
            channel_id=post.channel_id,
            message_id=post.id,
            text="pong",
        )


app = bot_app.create_fastapi_app()
```

Запустите приложение:

```bash
uvicorn bot:app --host 0.0.0.0 --port 8000
```

!!! note
    Это первая версия сайта. В следующих разделах появятся подробные руководства,
    справочник методов и примеры для кнопок, фильтров и состояний.

## Требования

- Python 3.10 или новее;
- Mattermost с HTTP API v4;
- токен бота Mattermost.
