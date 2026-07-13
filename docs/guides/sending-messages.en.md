# Sending messages

`MMBot` is an asynchronous client for direct Mattermost API calls. It is useful
for scripts, background jobs, and applications that do not process incoming
events.

## Send your first message

Provide the Mattermost address and token through environment variables:

```bash
export MATTERMOST_URL="https://mattermost.example.com"
export MATTERMOST_BOT_TOKEN="your-token"
export MATTERMOST_CHANNEL_ID="channel-id"
```

Create `send_message.py`:

```python title="send_message.py"
import asyncio
import os

from aiomost import MMBot


async def main() -> None:
    bot = MMBot(
        api_url=os.environ["MATTERMOST_URL"],
        bot_token=os.environ["MATTERMOST_BOT_TOKEN"],
    )

    post = await bot.send_message(
        channel_id=os.environ["MATTERMOST_CHANNEL_ID"],
        text="Hello from aiomost!",
    )
    print(f"Message sent: {post['id']}")


if __name__ == "__main__":
    asyncio.run(main())
```

Run the script:

```bash
python send_message.py
```

`send_message()` returns the Mattermost JSON response as a dictionary. It
contains the created post ID, channel ID, message text, and other post fields.

!!! note
    The guard must be written as `if __name__ == "__main__":`, with two
    underscores on each side.

## Reply in a thread

Pass the original post ID to `reply_message()`:

```python
reply = await bot.reply_message(
    channel_id="channel-id",
    message_id="root-post-id",
    text="A reply in the thread",
)
```

`message_id` becomes the root post of the thread.

## Send a direct message

`send_direct_message()` retrieves the bot ID, creates or finds a direct channel,
and sends the message:

```python
post = await bot.send_direct_message(
    user_id="mattermost-user-id",
    text="A direct message",
)
```

The method expects a user ID, not a username. Use `get_user_by_username()` to
look up a user by name:

```python
user = await bot.get_user_by_username("ivan")

if user is not None:
    await bot.send_direct_message(
        user_id=user.id,
        text="Hello, Ivan!",
    )
```

## Edit and delete a message

```python
await bot.edit_message(
    message_id="post-id",
    text="Updated text",
)

deleted_post = await bot.delete_message(message_id="post-id")
```

The token must belong to the message author or have sufficient Mattermost
permissions for these operations.

## Handle errors

When Mattermost responds with a status outside the `2xx` range, the client
raises `httpx.HTTPStatusError`:

```python
import httpx


try:
    await bot.send_message(
        channel_id="channel-id",
        text="Hello!",
    )
except httpx.HTTPStatusError as error:
    print(
        "Mattermost rejected the request:",
        error.response.status_code,
        error.response.text,
    )
```

The most common causes are missing channel access, an incorrect ID, or an
expired token.
