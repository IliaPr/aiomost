# Реакции

`aiomost-tools` поддерживает добавление, получение и удаление emoji-реакций
через Mattermost API v4, а также обработку событий WebSocket при изменении
реакций.

## Работа с API

Добавьте реакцию к сообщению:

```python
reaction = await bot.add_reaction(
    post_id="POST_ID",
    emoji_name="thumbsup",
)

print(reaction.user_id, reaction.emoji_name)
```

По умолчанию `user_id="me"`, то есть реакция создаётся от имени пользователя,
чей токен использует клиент. При необходимости ID можно передать явно.

Получите все реакции сообщения:

```python
reactions = await bot.get_reactions("POST_ID")

for reaction in reactions:
    print(reaction.user_id, reaction.emoji_name)
```

Удалите реакцию:

```python
await bot.remove_reaction(
    post_id="POST_ID",
    emoji_name="thumbsup",
)
```

## События WebSocket

Для входящих событий доступны два декоратора:

```python
from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()


@bot_app.reaction_added()
async def handle_added_reaction(event, bot):
    reaction = event.data.reaction
    await bot.reply_message(
        channel_id=event.broadcast.channel_id,
        message_id=reaction.post_id,
        text=f"Добавлена реакция :{reaction.emoji_name}:",
    )


@bot_app.reaction_removed()
async def handle_removed_reaction(event):
    reaction = event.data.reaction
    print(reaction.user_id, reaction.post_id, reaction.emoji_name)
```

Объект `Reaction` содержит основные поля Mattermost:

| Поле | Описание |
| --- | --- |
| `user_id` | Пользователь, добавивший или удаливший реакцию |
| `post_id` | Сообщение, к которому относится реакция |
| `emoji_name` | Имя emoji без двоеточий |
| `create_at` | Время создания в миллисекундах |

Для WebSocket listener требуется extra `websocket`.
