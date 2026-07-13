# Configuring a FastAPI application

`MattermostBotApp` can read its settings from the environment. This is the
recommended approach for a FastAPI application: the code stays the same across
environments while addresses and secrets are provided at startup.

## Environment variables

Create a local `.env` file:

```dotenv title=".env"
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_BOT_TOKEN=your-token
PUBLIC_BASE_URL=https://bot.example.com
```

Two variables are required:

| Variable | Purpose |
| --- | --- |
| `MATTERMOST_URL` | Base HTTP(S) address of the Mattermost server |
| `MATTERMOST_BOT_TOKEN` | Mattermost bot token |

`PUBLIC_BASE_URL` is required when the application sends interactive buttons.
It is the public address of the FastAPI application without the callback path.

!!! warning
    Add `.env` to `.gitignore`. If a token appears in Git, a log, or a message,
    revoke it in Mattermost and create a new one.

## Create the application

Load the settings with `from_env()`:

```python title="app.py"
from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()
app = bot_app.create_fastapi_app()
```

`app` is a regular FastAPI ASGI application. On startup it connects to the
Mattermost WebSocket; on shutdown it stops the background task cleanly. Event
handlers can be declared between the creation of `bot_app` and `app`.

## Run locally

The library does not load `.env` files itself. Load the variables into the
environment first, then start Uvicorn:

=== "Linux and macOS"

    ```bash
    set -a
    source .env
    set +a
    uvicorn app:app --reload
    ```

=== "Without an .env file"

    ```bash
    MATTERMOST_URL="https://mattermost.example.com" \
    MATTERMOST_BOT_TOKEN="your-token" \
    PUBLIC_BASE_URL="https://bot.example.com" \
    uvicorn app:app --reload
    ```

The application exposes two service endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Application health check |
| `POST` | `/mattermost/action` | Interactive button callback |

For callbacks, `PUBLIC_BASE_URL` must be reachable from the Mattermost server.
`127.0.0.1` is suitable for a health check, but not for buttons.

Check the application with:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "ok"}
```

## Optional integrations

Add Redis when using user states:

```dotenv title=".env"
REDIS_URL=redis://localhost:6379/0
```

The WebSocket URL is derived automatically from `MATTERMOST_URL`. Override it
only for a non-standard network setup:

```dotenv title=".env"
MATTERMOST_WS_URL=wss://mattermost.example.com/api/v4/websocket
```

All supported settings:

| Variable | Required | Purpose |
| --- | :---: | --- |
| `MATTERMOST_URL` | Yes | Mattermost address |
| `MATTERMOST_BOT_TOKEN` | Yes | Bot token |
| `PUBLIC_BASE_URL` | No | Public FastAPI application address |
| `REDIS_URL` | No | Redis connection URL |
| `MATTERMOST_WS_URL` | No | Custom WebSocket URL |
