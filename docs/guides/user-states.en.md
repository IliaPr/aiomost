# User states and data

User states let a bot split a conversation into steps. `MattermostBotApp` can
store the current state and arbitrary user data in Redis, then route messages
and button clicks to the handler for that state.

## Prerequisites

Install the Redis integration:

```bash
pip install "aiomost-tools[redis] @ git+https://github.com/IliaPr/aiomost.git"
```

Start Redis and provide its connection URL:

```dotenv title=".env"
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_BOT_TOKEN=your-token
REDIS_URL=redis://localhost:6379/0
```

`MattermostBotApp.from_env()` creates the state manager automatically when
`REDIS_URL` is set. Without a state manager, handlers that use
`required_state` do not match and the `state` argument is not injected.

## Define states

Group related states by subclassing `StatesGroup`:

```python title="states.py"
from aiomost import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
```

The attribute name becomes the state name. The values stored in Redis for this
example are `Registration:waiting_for_name` and
`Registration:waiting_for_email`.

States can also have an explicit name:

```python
class Support(StatesGroup):
    waiting_for_details = State("details")
```

## Start a dialog

Request the injected `state` manager in a handler, save the first state for the
user, and ask the first question:

```python title="app.py"
from aiomost import MattermostBotApp

from states import Registration


bot_app = MattermostBotApp.from_env()


@bot_app.message()
async def start_registration(event, bot, state):
    post = event.data.post

    if (post.message or "").strip() != "!register":
        return

    await state.set_state(post.user_id, Registration.waiting_for_name)
    await bot.reply_message(
        channel_id=post.channel_id,
        message_id=post.id,
        text="What is your name?",
    )
```

Only parameters declared in the handler signature are injected. The name
`state` refers to the configured `RedisStateManager` instance.

## Handle each step

Use `required_state` to run a handler only when the user is at a particular
step:

```python
@bot_app.message(required_state=Registration.waiting_for_name)
async def save_name(event, bot, state):
    post = event.data.post
    name = (post.message or "").strip()

    await state.update_data(post.user_id, name=name)
    await state.set_state(post.user_id, Registration.waiting_for_email)
    await bot.reply_message(
        channel_id=post.channel_id,
        message_id=post.id,
        text="What is your email address?",
    )


@bot_app.message(required_state=Registration.waiting_for_email)
async def save_email(event, bot, state):
    post = event.data.post
    email = (post.message or "").strip()

    await state.update_data(post.user_id, email=email)
    data = await state.get_data(post.user_id)
    await state.delete_state(post.user_id)

    await bot.reply_message(
        channel_id=post.channel_id,
        message_id=post.id,
        text=f"Registration complete for {data['name']} ({data['email']}).",
    )
```

When a state is active, its matching handler has priority over handlers without
`required_state`. After a regular handler changes the state, processing of the
current event stops so the next step receives the next event.

`delete_state()` and its alias `reset_user_state()` clear only the current
state. Stored user data remains available until it expires or is overwritten.

## Store user data

`update_data()` merges new fields with the JSON object already stored for the
user:

```python
await state.update_data(user_id, name="Ada")
await state.update_data(user_id, email="ada@example.com")

data = await state.get_data(user_id)
# {"name": "Ada", "email": "ada@example.com"}
```

`get_data()` returns an empty dictionary when no data is stored. Values passed
to `update_data()` must be JSON serializable.

## Use states with buttons

Button handlers support the same `required_state` argument:

```python
@bot_app.button("registration:cancel", required_state=Registration.waiting_for_email)
async def cancel_registration(event, state):
    await state.reset_user_state(event.user_id)
    return {"update": {"message": "Registration cancelled"}}
```

The user ID is read from the Mattermost callback payload, so state routing
works for both `posted` and `button_query` events.

## Configure expiration

For a default TTL, create the state manager explicitly and pass it to the
application:

```python
from aiomost import MattermostBotApp
from aiomost.mattermost_state_storage.redis_state_manager import RedisStateManager


state_manager = RedisStateManager.from_url(
    "redis://localhost:6379/0",
    default_expiry_seconds=3600,
)

bot_app = MattermostBotApp(
    mattermost_url="https://mattermost.example.com",
    bot_token="your-token",
    state_manager=state_manager,
)
```

Override the default for an individual operation when necessary:

```python
await state.set_state(user_id, Registration.waiting_for_name, expiry_seconds=600)
await state.update_data(user_id, expiry_seconds=600, name="Ada")
```

State and data use separate Redis keys and therefore have independent TTLs.
Passing both `state_manager` and `redis_url` to `MattermostBotApp` raises
`ValueError`.
