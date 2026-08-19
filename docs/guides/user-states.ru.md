# Состояния и данные пользователей

Состояния позволяют разделить диалог с ботом на последовательные шаги.
`MattermostBotApp` может хранить текущее состояние и произвольные данные
пользователя в Redis, а затем направлять сообщения и нажатия кнопок в
обработчик соответствующего состояния.

## Предварительная настройка

Установите интеграцию с Redis:

```bash
pip install "aiomost-tools[redis] @ git+https://github.com/IliaPr/aiomost.git"
```

Запустите Redis и укажите URL подключения:

```dotenv title=".env"
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_BOT_TOKEN=your-token
REDIS_URL=redis://localhost:6379/0
```

Если задан `REDIS_URL`, метод `MattermostBotApp.from_env()` автоматически
создаёт менеджер состояний. Без него обработчики с `required_state` не
срабатывают, а аргумент `state` не внедряется.

## Объявление состояний

Объедините связанные состояния в подклассе `StatesGroup`:

```python title="states.py"
from aiomost import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
```

Имя атрибута становится именем состояния. В этом примере в Redis сохраняются
значения `Registration:waiting_for_name` и
`Registration:waiting_for_email`.

Состоянию также можно задать явное имя:

```python
class Support(StatesGroup):
    waiting_for_details = State("details")
```

## Начало диалога

Запросите менеджер `state` в аргументах обработчика, сохраните первое
состояние пользователя и задайте первый вопрос:

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
        text="Как вас зовут?",
    )
```

В обработчик внедряются только объявленные в его сигнатуре параметры. Под
именем `state` передаётся настроенный экземпляр `RedisStateManager`.

## Обработка шагов

Используйте `required_state`, чтобы запускать обработчик только на определённом
шаге:

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
        text="Укажите адрес электронной почты.",
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
        text=f"Регистрация завершена: {data['name']} ({data['email']}).",
    )
```

Если состояние активно, соответствующий ему обработчик имеет приоритет перед
обработчиками без `required_state`. Когда обычный обработчик изменяет
состояние, обработка текущего события прекращается: следующий шаг получит уже
следующее событие.

Методы `delete_state()` и `reset_user_state()` удаляют только текущее
состояние. Данные пользователя сохраняются, пока не истечёт их TTL или они не
будут перезаписаны.

## Хранение данных пользователя

Метод `update_data()` объединяет новые поля с уже сохранённым для пользователя
JSON-объектом:

```python
await state.update_data(user_id, name="Ада")
await state.update_data(user_id, email="ada@example.com")

data = await state.get_data(user_id)
# {"name": "Ада", "email": "ada@example.com"}
```

Если данных нет, `get_data()` возвращает пустой словарь. Значения,
передаваемые в `update_data()`, должны поддерживать сериализацию в JSON.

## Состояния и кнопки

Обработчики кнопок поддерживают тот же аргумент `required_state`:

```python
@bot_app.button("registration:cancel", required_state=Registration.waiting_for_email)
async def cancel_registration(event, state):
    await state.reset_user_state(event.user_id)
    return {"update": {"message": "Регистрация отменена"}}
```

ID пользователя извлекается из callback-данных Mattermost, поэтому
маршрутизация по состоянию работает как для событий `posted`, так и для
`button_query`.

## Настройка времени хранения

Чтобы задать TTL по умолчанию, создайте менеджер состояний явно и передайте его
приложению:

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

При необходимости переопределите TTL для отдельной операции:

```python
await state.set_state(user_id, Registration.waiting_for_name, expiry_seconds=600)
await state.update_data(user_id, expiry_seconds=600, name="Ада")
```

Состояние и данные хранятся в разных ключах Redis, поэтому их TTL независимы.
Если одновременно передать `state_manager` и `redis_url` в
`MattermostBotApp`, будет вызвано исключение `ValueError`.
