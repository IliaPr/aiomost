# Обработка событий

`MattermostBotApp` получает события Mattermost через WebSocket и передаёт их
асинхронным обработчикам. Регистрируйте обработчики до вызова
`create_fastapi_app()`.

## Обработчик сообщений

Используйте `message()` для обработки новых сообщений:

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
            text=f"Привет, {event.data.sender_name}!",
        )


app = bot_app.create_fastapi_app()
```

Первым аргументом обработчик всегда получает событие. Дополнительные зависимости
передаются только тогда, когда они присутствуют в сигнатуре функции.

## Аргументы обработчика

Обработчик может запросить следующие аргументы:

| Аргумент | Значение |
| --- | --- |
| `event` | Входящее событие Mattermost |
| `bot` | Настроенный клиент `MMBot` |
| `app` | Текущий экземпляр `MattermostBotApp` |
| `state` | Менеджер состояний, если хранилище состояний подключено |

Указывайте только необходимые обработчику аргументы:

```python
@bot_app.message()
async def log_message(event):
    print(event.data.post.message)


@bot_app.message()
async def answer_message(event, bot, app):
    ...
```

## Событие сообщения

В событии `posted` сообщение доступно через `event.data.post`.

Основные поля:

| Поле | Описание |
| --- | --- |
| `post.id` | ID сообщения |
| `post.user_id` | ID автора |
| `post.channel_id` | ID канала |
| `post.message` | Текст сообщения |
| `post.root_id` | ID корневого сообщения для ответа в треде; пустое для корневого сообщения |
| `post.file_ids` | ID прикреплённых файлов |
| `event.data.sender_name` | Username отправителя |
| `event.data.channel_name` | Название канала |
| `event.data.team_id` | ID команды |

Ответ в треде можно определить по `root_id`:

```python
@bot_app.message()
async def handle_root_posts(event):
    post = event.data.post

    if post.root_id:
        return

    print("Новое корневое сообщение:", post.message)
```

## Фильтры

Фильтр — асинхронный вызываемый объект, который получает событие и возвращает
`True`, если обработчик должен быть запущен. Переиспользуемые фильтры с
параметрами удобно объявлять как классы:

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

Несколько фильтров объединяются по принципу AND: каждый из них должен вернуть
`True`.

```python
class RootPost:
    async def __call__(self, event) -> bool:
        return not event.data.post.root_id


@bot_app.message(Command("!ping"), RootPost())
async def root_ping(event, bot):
    ...
```

!!! tip
    Не добавляйте в фильтры побочные эффекты. Фильтр должен только проверить
    событие и определить, подходит ли оно обработчику.

## Добавление пользователя

Используйте `user_added()`, когда пользователь присоединяется к каналу или
команде:

```python
@bot_app.user_added()
async def handle_user_added(event, bot):
    user_id = event.data.user_id
    team_id = event.data.team_id

    print(f"Пользователь {user_id} добавлен в команду {team_id}")
```

## Регистрация события по имени

`event()` регистрирует обработчик по имени observer-а. Это полезно, если для
события нет отдельного высокоуровневого декоратора:

```python
@bot_app.event("posted")
async def handle_posted(event):
    print(event.data.post.message)
```

Поддерживаются имена `message`, `posted`, `user_added`, `button_query` и
`error`. При передаче другого имени во время регистрации возникнет `ValueError`.

Для обычных сообщений используйте `message()`: он напрямую соответствует
событию Mattermost `posted` и понятнее описывает назначение обработчика.

## Порядок обработчиков

Обработчики запускаются в порядке регистрации. Если обработчик возвращает
значение, отличное от `None`, распространение события прекращается, а значение
становится результатом диспетчеризации. Обработчик, который только выполняет
действие, обычно возвращает `None`, поэтому после него может быть вызван следующий
подходящий обработчик.
