# Installation

The base installation includes the HTTP client, routers, dispatcher, event
models, and helpers for building interactive buttons.

## Base installation

The package is currently distributed through GitHub:

=== "pip"

    ```bash
    pip install "aiomost-tools @ git+https://github.com/IliaPr/aiomost.git"
    ```

=== "Poetry"

    ```bash
    poetry add "git+https://github.com/IliaPr/aiomost.git"
    ```

## Optional features

Additional dependencies are installed through extras:

| Extra | Dependencies | Purpose |
| --- | --- | --- |
| `fastapi` | FastAPI, Uvicorn | HTTP endpoint for button callbacks |
| `websocket` | websockets | Real-time Mattermost events |
| `redis` | redis | User state and data storage |
| `all` | All dependencies above | Complete installation |

For a regular bot with FastAPI and WebSocket support:

```bash
pip install "aiomost-tools[fastapi,websocket] @ git+https://github.com/IliaPr/aiomost.git"
```

For a project with Redis-backed state storage:

```bash
pip install "aiomost-tools[fastapi,websocket,redis] @ git+https://github.com/IliaPr/aiomost.git"
```

To install every integration:

```bash
pip install "aiomost-tools[all] @ git+https://github.com/IliaPr/aiomost.git"
```

!!! tip
    Install only the extras you need. The base installation is enough to send
    messages with `MMBot`.

## Verify the installation

```bash
python -c "import aiomost; print(aiomost.__version__)"
```

The command should print the installed library version without import errors.

## Next step

After installation, provide the Mattermost URL and bot token as described in
the Configuration section.
