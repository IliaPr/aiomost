# Handling events

`MattermostBotApp` receives Mattermost events over WebSocket and routes them to
asynchronous handlers. Register handlers before calling
`create_fastapi_app()`.

## Message handler

Use `message()` to handle new posts:

```python title="app.py"
from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()


@bot_app.message()
async def handle_message(event, bot):
    post = event.data.post
    text = (post.message or "").strip()

    if text == "!hello":
        await bot.send_message(
            channel_id=post.channel_id,
            text=f"Hello, {event.data.sender_name}!",
        )


app = bot_app.create_fastapi_app()
```

The first argument is always the event. Additional dependencies are injected
only when they are present in the handler signature.

## Handler arguments

A handler can request the following arguments:

| Argument | Value |
| --- | --- |
| `event` | The incoming Mattermost event |
| `bot` | The configured `MMBot` client |
| `app` | The current `MattermostBotApp` instance |
| `state` | The configured state manager, when state storage is enabled |

Use only the arguments required by the handler:

```python
@bot_app.message()
async def log_message(event):
    print(event.data.post.message)


@bot_app.message()
async def answer_message(event, bot, app):
    ...
```

## Message event

For a `posted` event, the message is available as `event.data.post`.

Common fields:

| Field | Description |
| --- | --- |
| `post.id` | Post ID |
| `post.user_id` | Author ID |
| `post.channel_id` | Channel ID |
| `post.message` | Message text |
| `post.root_id` | Root post ID for a thread reply; empty for a root post |
| `post.file_ids` | IDs of attached files |
| `event.data.sender_name` | Sender username |
| `event.data.channel_name` | Channel name |
| `event.data.team_id` | Team ID |

Thread replies can be detected with `root_id`:

```python
@bot_app.message()
async def handle_root_posts(event):
    post = event.data.post

    if post.root_id:
        return

    print("New root post:", post.message)
```

## Filters

A filter is an asynchronous callable that receives the event and returns
`True` when the handler should run. Reusable parameterized filters can be
defined as classes:

```python
class Command:
    def __init__(self, name: str) -> None:
        self.name = name

    async def __call__(self, event) -> bool:
        text = (event.data.post.message or "").strip()
        return text == self.name


@bot_app.message(Command("!ping"))
async def ping(event, bot):
    await bot.send_message(
        channel_id=event.data.post.channel_id,
        text="pong",
    )
```

Multiple filters use AND logic: every filter must return `True`.

```python
class RootPost:
    async def __call__(self, event) -> bool:
        return not event.data.post.root_id


@bot_app.message(Command("!ping"), RootPost())
async def root_ping(event, bot):
    ...
```

!!! tip
    Keep filters free of side effects. Their job is to inspect an event and
    decide whether a handler matches it.

## User added event

Use `user_added()` when a user joins a channel or team:

```python
@bot_app.user_added()
async def handle_user_added(event, bot):
    user_id = event.data.user_id
    team_id = event.data.team_id

    print(f"User {user_id} was added to team {team_id}")
```

## Generic event registration

`event()` registers a handler by the observer name. It is useful when the
high-level decorator is not available:

```python
@bot_app.event("posted")
async def handle_posted(event):
    print(event.data.post.message)
```

Supported observer names are `message`, `posted`, `user_added`, `button_query`,
and `error`. Passing another name raises `ValueError` during registration.

For regular messages, prefer `message()`; it maps directly to Mattermost's
`posted` event and makes the handler's purpose clearer.

## Handler order

Handlers run in registration order. If a handler returns a non-`None` value,
event propagation stops and that value becomes the dispatch result. A handler
that only performs an action normally returns `None`, allowing the next
matching handler to run.
