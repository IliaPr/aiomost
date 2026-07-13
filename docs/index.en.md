# aiomost-tools

An asynchronous Python toolkit for building Mattermost bots.

[Install](getting-started/installation.md){ .md-button .md-button--primary }
[GitHub](https://github.com/IliaPr/aiomost){ .md-button }

## Features

- asynchronous Mattermost HTTP API v4 client;
- event routing and handler filters;
- interactive buttons and callbacks;
- real-time events over WebSocket;
- FastAPI integration;
- Redis-backed user state storage.

## Quick start

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

Run the application:

```bash
uvicorn bot:app --host 0.0.0.0 --port 8000
```

!!! note
    This is the first version of the documentation. Detailed API reference and
    guides for buttons, filters, and states will be added in upcoming sections.

## Requirements

- Python 3.10 or newer;
- Mattermost with HTTP API v4;
- a Mattermost bot token.
