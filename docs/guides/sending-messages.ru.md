# Отправка сообщений

`MMBot` — асинхронный клиент для прямых вызовов Mattermost API. Он подходит для
скриптов, фоновых задач и приложений, которым не требуется обработка входящих
событий.

## Первое сообщение

Передайте адрес Mattermost и токен через переменные окружения:

```bash
export MATTERMOST_URL="https://mattermost.example.com"
export MATTERMOST_BOT_TOKEN="your-token"
export MATTERMOST_CHANNEL_ID="channel-id"
```

Создайте файл `send_message.py`:

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
    print(f"Сообщение отправлено: {post['id']}")


if __name__ == "__main__":
    asyncio.run(main())
```

Запустите скрипт:

```bash
python send_message.py
```

`send_message()` возвращает JSON-ответ Mattermost как словарь. В нём доступны
ID созданного сообщения, ID канала, текст и другие поля поста.

!!! note
    Конструкция должна записываться как `if __name__ == "__main__":` — с двумя
    символами подчёркивания с каждой стороны.

## Ответ в треде

Для ответа на сообщение передайте ID исходного поста в `reply_message()`:

```python
reply = await bot.reply_message(
    channel_id="channel-id",
    message_id="root-post-id",
    text="Ответ в треде",
)
```

`message_id` станет корневым сообщением треда.

## Личное сообщение

`send_direct_message()` самостоятельно получает ID бота, создаёт или находит
личный канал и отправляет сообщение:

```python
post = await bot.send_direct_message(
    user_id="mattermost-user-id",
    text="Личное сообщение",
)
```

Методу нужен ID пользователя, а не username. Найти пользователя по имени можно
через `get_user_by_username()`:

```python
user = await bot.get_user_by_username("ivan")

if user is not None:
    await bot.send_direct_message(
        user_id=user.id,
        text="Привет, Иван!",
    )
```

## Редактирование и удаление

```python
await bot.edit_message(
    message_id="post-id",
    text="Исправленный текст",
)

deleted_post = await bot.delete_message(message_id="post-id")
```

Для этих операций токен должен принадлежать автору сообщения или иметь
достаточные права в Mattermost.

## Обработка ошибок

При ответе Mattermost вне диапазона `2xx` клиент вызывает исключение
`httpx.HTTPStatusError`:

```python
import httpx


try:
    await bot.send_message(
        channel_id="channel-id",
        text="Hello!",
    )
except httpx.HTTPStatusError as error:
    print(
        "Mattermost отклонил запрос:",
        error.response.status_code,
        error.response.text,
    )
```

На практике обычно проверяют доступ бота к каналу, корректность ID и срок
действия токена.
