# Интерактивные кнопки

Mattermost позволяет прикреплять к сообщению интерактивные кнопки и отправляет
HTTP callback, когда пользователь нажимает одну из них. `MattermostBotApp`
создаёт как данные кнопок, так и FastAPI endpoint для callback-ов.

## Предварительная настройка

Установите интеграцию с FastAPI и настройте публичный адрес приложения:

```dotenv title=".env"
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_BOT_TOKEN=your-token
PUBLIC_BASE_URL=https://bot.example.com
```

`PUBLIC_BASE_URL` должен быть доступен серверу Mattermost. По умолчанию
callback URL выглядит так:

```text
https://bot.example.com/mattermost/action
```

## Отправка кнопки

Создайте actions через `app.actions()` и передайте их методу отправки сообщения:

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
            text="Продолжить?",
            actions=app.actions(
                [
                    ("confirm_yes", "Да", "confirm"),
                    ("confirm_no", "Нет", "cancel"),
                ]
            ),
        )


app = bot_app.create_fastapi_app()
```

Каждая кнопка задаётся кортежем из трёх значений:

```python
(button_id, label, action)
```

| Значение | Назначение |
| --- | --- |
| `button_id` | ID, сохраняемый во вложении Mattermost |
| `label` | Текст, который видит пользователь |
| `action` | Значение, передаваемое обработчику callback-а |

Для маршрутизации нажатий обычно используется значение `action`.

## Обработка нажатия

Зарегистрируйте callback через `button()`:

```python
@bot_app.button("confirm")
async def confirm_action(event):
    return {
        "update": {
            "message": "Подтверждено",
        }
    }


@bot_app.button("cancel")
async def cancel_action(event):
    return {
        "update": {
            "message": "Отменено",
        }
    }
```

Строка, переданная в `button()`, должна совпадать с третьим значением кортежа
кнопки:

```python
("confirm_yes", "Да", "confirm")
#                           └── @bot_app.button("confirm")
```

Ответ с полем `update` заменяет содержимое исходного интерактивного сообщения
в Mattermost.

## Событие кнопки

Обработчик получает объект `MattermostButtonQuery`. Основные поля доступны
непосредственно в событии:

| Поле | Описание |
| --- | --- |
| `event.action` | Значение action, назначенное кнопке |
| `event.user_id` | ID пользователя, нажавшего кнопку |
| `event.channel_id` | Канал, содержащий сообщение |
| `event.post_id` | ID интерактивного сообщения |
| `event.team_id` | ID команды, если Mattermost передал его |
| `event.trigger_id` | Trigger ID из callback-а |
| `event.data` | Полные данные callback-а |

Пример:

```python
@bot_app.button("confirm")
async def confirm_action(event, bot):
    await bot.send_ephemeral_message(
        user_id=event.user_id,
        channel_id=event.channel_id,
        text="Ваш выбор сохранён",
    )

    return {
        "update": {
            "message": f"Подтверждено пользователем {event.user_id}",
        }
    }
```

## Динамические actions

`button()` также принимает синхронный предикат. Он получает строку action и
возвращает `True`, если обработчик должен быть запущен:

```python
@bot_app.button(lambda action: action.startswith("ticket:"))
async def select_ticket(event):
    ticket_id = event.action.removeprefix("ticket:")

    return {
        "update": {
            "message": f"Выбрана задача: {ticket_id}",
        }
    }
```

Создайте соответствующую кнопку динамически:

```python
ticket_id = "TASK-42"

actions = bot_app.actions(
    [
        (
            f"open_{ticket_id}",
            "Открыть задачу",
            f"ticket:{ticket_id}",
        )
    ]
)
```

## Пользовательский путь callback-а

Если приложение использует другой путь callback-а, укажите одинаковое значение
при создании actions и FastAPI-приложения:

```python
action_path = "/callbacks/mattermost"

actions = bot_app.actions(
    [("confirm", "Подтвердить", "confirm")],
    action_path=action_path,
)

app = bot_app.create_fastapi_app(action_path=action_path)
```

Итоговый callback URL:

```text
https://bot.example.com/callbacks/mattermost
```

!!! warning
    Пути в `actions()` и `create_fastapi_app()` должны совпадать. Иначе
    Mattermost отправит callback кнопки на несуществующий endpoint.

## Переопределение публичного URL

Используйте `base_url`, если для конкретного сообщения требуется другой адрес
приложения:

```python
actions = bot_app.actions(
    [("confirm", "Подтвердить", "confirm")],
    base_url="https://staging-bot.example.com",
)
```

Этот параметр переопределяет `PUBLIC_BASE_URL` только для созданных actions.
