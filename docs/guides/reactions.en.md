# Reactions

`aiomost-tools` supports adding, listing, and removing emoji reactions through
the Mattermost API v4, as well as handling WebSocket events when reactions
change.

## API methods

Add a reaction to a post:

```python
reaction = await bot.add_reaction(
    post_id="POST_ID",
    emoji_name="thumbsup",
)

print(reaction.user_id, reaction.emoji_name)
```

The default `user_id="me"` creates the reaction for the user represented by the
client token. You can also pass an explicit user ID.

List all reactions on a post:

```python
reactions = await bot.get_reactions("POST_ID")

for reaction in reactions:
    print(reaction.user_id, reaction.emoji_name)
```

Remove a reaction:

```python
await bot.remove_reaction(
    post_id="POST_ID",
    emoji_name="thumbsup",
)
```

## WebSocket events

Two decorators are available for incoming events:

```python
from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()


@bot_app.reaction_added()
async def handle_added_reaction(event, bot):
    reaction = event.data.reaction
    await bot.reply_message(
        channel_id=event.broadcast.channel_id,
        message_id=reaction.post_id,
        text=f"Reaction :{reaction.emoji_name}: added",
    )


@bot_app.reaction_removed()
async def handle_removed_reaction(event):
    reaction = event.data.reaction
    print(reaction.user_id, reaction.post_id, reaction.emoji_name)
```

The `Reaction` object exposes the main Mattermost fields:

| Field | Description |
| --- | --- |
| `user_id` | User who added or removed the reaction |
| `post_id` | Post the reaction belongs to |
| `emoji_name` | Emoji name without colons |
| `create_at` | Creation time in milliseconds |

The WebSocket listener requires the `websocket` extra.
