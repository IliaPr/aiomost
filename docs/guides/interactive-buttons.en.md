# Interactive buttons

Mattermost can attach interactive buttons to a post and send an HTTP callback
when a user clicks one. `MattermostBotApp` creates both the button payload and
the FastAPI callback endpoint.

## Prerequisites

Install the FastAPI integration and configure a public application URL:

```dotenv title=".env"
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_BOT_TOKEN=your-token
PUBLIC_BASE_URL=https://bot.example.com
```

`PUBLIC_BASE_URL` must be reachable from the Mattermost server. The default
callback URL is:

```text
https://bot.example.com/mattermost/action
```

## Send a button

Create actions with `app.actions()` and pass them to a message method:

```python title="app.py"
from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()


@bot_app.message()
async def handle_message(event, bot, app):
    post = event.data.post

    if (post.message or "").strip() == "!confirm":
        await bot.reply_message(
            channel_id=post.channel_id,
            message_id=post.id,
            text="Continue?",
            actions=app.actions(
                [
                    ("confirm_yes", "Yes", "confirm"),
                    ("confirm_no", "No", "cancel"),
                ]
            ),
        )


app = bot_app.create_fastapi_app()
```

Each button is a tuple containing three values:

```python
(button_id, label, action)
```

| Value | Purpose |
| --- | --- |
| `button_id` | ID stored in the Mattermost attachment |
| `label` | Text displayed to the user |
| `action` | Value sent to the callback handler |

The `action` value is the part normally used to route button clicks.

## Handle a click

Register a callback with `button()`:

```python
@bot_app.button("confirm")
async def confirm_action(event):
    return {
        "update": {
            "message": "Confirmed",
        }
    }


@bot_app.button("cancel")
async def cancel_action(event):
    return {
        "update": {
            "message": "Cancelled",
        }
    }
```

The string passed to `button()` must match the third value of the button tuple:

```python
("confirm_yes", "Yes", "confirm")
#                            └── @bot_app.button("confirm")
```

Returning an `update` response replaces the original interactive post content
in Mattermost.

## Button event

The handler receives `MattermostButtonQuery`. Common fields are available
directly on the event:

| Field | Description |
| --- | --- |
| `event.action` | Action value assigned to the button |
| `event.user_id` | ID of the user who clicked it |
| `event.channel_id` | Channel containing the post |
| `event.post_id` | Interactive post ID |
| `event.team_id` | Team ID, when provided by Mattermost |
| `event.trigger_id` | Trigger ID provided with the callback |
| `event.data` | Complete callback payload |

Example:

```python
@bot_app.button("confirm")
async def confirm_action(event, bot):
    await bot.send_ephemeral_message(
        user_id=event.user_id,
        channel_id=event.channel_id,
        text="Your choice was saved",
    )

    return {
        "update": {
            "message": f"Confirmed by user {event.user_id}",
        }
    }
```

## Dynamic actions

`button()` also accepts a synchronous predicate. It receives the action string
and returns `True` when the handler should run:

```python
@bot_app.button(lambda action: action.startswith("ticket:"))
async def select_ticket(event):
    ticket_id = event.action.removeprefix("ticket:")

    return {
        "update": {
            "message": f"Selected ticket: {ticket_id}",
        }
    }
```

Create the corresponding button dynamically:

```python
ticket_id = "TASK-42"

actions = bot_app.actions(
    [
        (
            f"open_{ticket_id}",
            "Open ticket",
            f"ticket:{ticket_id}",
        )
    ]
)
```

## Custom callback path

If the application uses a different callback path, configure the same value
when creating actions and the FastAPI application:

```python
action_path = "/callbacks/mattermost"

actions = bot_app.actions(
    [("confirm", "Confirm", "confirm")],
    action_path=action_path,
)

app = bot_app.create_fastapi_app(action_path=action_path)
```

The resulting callback URL is:

```text
https://bot.example.com/callbacks/mattermost
```

!!! warning
    The path used by `actions()` and `create_fastapi_app()` must match.
    Otherwise, Mattermost will send button callbacks to a missing endpoint.

## Override the public URL

Use `base_url` when a particular message must point to another application
address:

```python
actions = bot_app.actions(
    [("confirm", "Confirm", "confirm")],
    base_url="https://staging-bot.example.com",
)
```

This overrides `PUBLIC_BASE_URL` only for the generated actions.
