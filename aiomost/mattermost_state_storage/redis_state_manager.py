# redis_state_manager.py
# Модуль для управления состоянием пользователей в Redis (без зависимости от config.py).

import redis.asyncio as redis
import json
from functools import wraps
from .matter_states import State  # Оставляем импорт State для type hinting
from urllib.parse import urlparse


class RedisStateManager:
    """
    Класс для управления состоянием пользователей в Redis (без зависимости от config.py).
    """

    def __init__(self, host=None, port=None, db=None, default_expiry_seconds=None):
        """
        Инициализирует RedisStateManager.

        Args:
            host: Хост Redis (строка, например, "localhost").
            port: Порт Redis (целое число, например, 6379).
            db: Номер базы данных Redis (целое число, например, 0).
            default_expiry_seconds: Дефолтное время жизни состояния в секундах (None = без ограничения).

        Теперь параметры подключения к Redis должны передаваться явно при инициализации,
        или через from_url. Значения по умолчанию из config.py убраны.
        """
        self.redis_host = host
        self.redis_port = port
        self.redis_db = db
        self.default_expiry_seconds = default_expiry_seconds

        if not any([host, port, db]):  # Проверяем, что хотя бы что-то задано явно в __init__
            print(
                "Warning: RedisStateManager initialized without explicit host, port, or db."
                "You must use from_url or set these attributes manually later."
            )

    @classmethod
    def from_url(cls, url: str, default_expiry_seconds=None):
        """
        Создает RedisStateManager из URL подключения к Redis.

        Args:
            url: URL подключения к Redis в формате redis://[username:password@]host[:port]/[db]
            default_expiry_seconds: Дефолтное время жизни состояния в секундах (None = без ограничения).

        Returns:
            RedisStateManager: Экземпляр RedisStateManager, подключенный к Redis по URL.
        """
        parsed_url = urlparse(url)
        host = parsed_url.hostname  # Теперь берем только из URL, значения по умолчанию нет
        port = parsed_url.port      # Теперь берем только из URL, значения по умолчанию нет
        # db может быть None
        db = int(parsed_url.path.strip('/')) if parsed_url.path else None

        return cls(host=host, port=port, db=db, default_expiry_seconds=default_expiry_seconds)

    async def get_state(self, user_id):
        """Асинхронно получает состояние пользователя из Redis."""
        r = redis.Redis(host=self.redis_host,
                        port=self.redis_port, db=self.redis_db)
        try:
            state_name_str = await r.get(f"state:{user_id}")
            if state_name_str:
                return state_name_str.decode('utf-8')
            return None
        finally:
            await r.close()

    async def set_state(self, user_id, state: State, expiry_seconds=None):
        """
        Асинхронно сохраняет состояние пользователя в Redis.

        Args:
            user_id: ID пользователя
            state: Состояние для сохранения
            expiry_seconds: Время жизни состояния в секундах. 
                           Если None, используется default_expiry_seconds из __init__.
                           Если и он None, состояние хранится без ограничения времени.
        """
        r = redis.Redis(host=self.redis_host,
                        port=self.redis_port, db=self.redis_db)
        try:
            state_name_str = state.state
            # Используем явно указанный expiry_seconds, иначе дефолтный, иначе без TTL
            ttl = expiry_seconds if expiry_seconds is not None else self.default_expiry_seconds
            if ttl is not None:
                await r.setex(f"state:{user_id}", ttl, state_name_str)
            else:
                await r.set(f"state:{user_id}", state_name_str)
        finally:
            await r.close()

    async def delete_state(self, user_id):
        """Асинхронно удаляет состояние пользователя из Redis."""
        r = redis.Redis(host=self.redis_host,
                        port=self.redis_port, db=self.redis_db)
        try:
            await r.delete(f"state:{user_id}")
        finally:
            await r.close()

    async def reset_user_state(self, user_id):
        """Сбрасывает состояние пользователя, удаляя его из Redis."""
        await self.delete_state(user_id)

    def get_user_id_from_event(self, event):
        """Извлекает user_id из объекта event MattermostUpdate."""
        # print(event)
        if event.event_type == "button_query":
            # Для события button_query user_id можно найти в data, в котором содержится информация о кнопке
            user_id = event.data.get("user_id")
            # print(f"Получен user_id для button_query: {user_id}")
            return user_id
        elif event.event_type == "posted":
            return event.data.post.user_id
        else:
            # Для других типов событий (например, сообщение)
            data = event.data
            post_data = json.loads(data["data"]["post"])
            return post_data.get("user_id")

    async def update_data(self, user_id: str = None, expiry_seconds=None, **data):
        """
        Обновляет (или создаёт) данные пользователя в Redis.

        Args:
            user_id: ID пользователя (может быть передан как позиционный аргумент или как именованный в **data)
            expiry_seconds: Время жизни данных в секундах. 
                           Если None, используется default_expiry_seconds из __init__.
                           Если и он None, данные хранятся без ограничения времени.
            **data: Данные для обновления. Если user_id передан как именованный аргумент (user_id=...), 
                   он будет извлечен из data.

        Примеры использования:
            await state.update_data(user_id, key=value)  # user_id позиционно
            await state.update_data(user_id=user_id, key=value)  # user_id как именованный
            await state.update_data(user_id, expiry_seconds=3600, key=value)  # с TTL
        """
        r = redis.Redis(host=self.redis_host,
                        port=self.redis_port, db=self.redis_db)

        try:
            # Если user_id не передан позиционно, пытаемся извлечь из data
            if user_id is None:
                user_id = data.pop('user_id', None)
                if user_id is None:
                    raise ValueError(
                        "user_id must be provided either as positional argument or as keyword argument (user_id=...)")

            # Удаляем expiry_seconds из data, если он там случайно оказался
            data.pop('expiry_seconds', None)

            key = f"data:{user_id}"

            # Получаем старые данные, если они есть
            existing_data = await r.get(key)
            if existing_data:
                existing_data = json.loads(existing_data)  # Декодируем JSON
            else:
                existing_data = {}  # Если данных нет, создаём пустой словарь

            # Обновляем словарь новыми данными
            existing_data.update(data)

            # Используем явно указанный expiry_seconds, иначе дефолтный, иначе без TTL
            ttl = expiry_seconds if expiry_seconds is not None else self.default_expiry_seconds
            if ttl is not None:
                await r.setex(key, ttl, json.dumps(existing_data))
            else:
                await r.set(key, json.dumps(existing_data))

        finally:
            await r.close()  # Закрываем соединение с Redis

    async def get_data(self, user_id: str):
        """Получает данные пользователя из Redis."""
        r = redis.Redis(host=self.redis_host,
                        port=self.redis_port, db=self.redis_db)

        try:
            key = f"data:{user_id}"
            data = await r.get(key)
            if data:
                return json.loads(data)
            return {}
        finally:
            await r.close()


def required_state(state: State, state_manager: RedisStateManager):
    """
    Декоратор для роутеров. Проверяет, соответствует ли текущее состояние пользователя заданному состоянию.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            event = kwargs.get('event')
            if event:
                user_id = state_manager.get_user_id_from_event(event)
                if user_id:
                    current_state_str = await state_manager.get_state(user_id)
                    if current_state_str == state.state:
                        return await func(*args, **kwargs)
            return None
        return decorator
    return decorator
