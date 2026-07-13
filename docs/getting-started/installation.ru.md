# Установка

Базовая установка содержит HTTP-клиент, роутеры, диспетчер, модели событий и
инструменты для создания интерактивных кнопок.

## Базовая установка

Пока пакет распространяется через GitHub:

=== "pip"

    ```bash
    pip install "aiomost-tools @ git+https://github.com/IliaPr/aiomost.git"
    ```

=== "Poetry"

    ```bash
    poetry add "git+https://github.com/IliaPr/aiomost.git"
    ```

## Опциональные возможности

Дополнительные зависимости устанавливаются через extras:

| Extra | Что устанавливается | Для чего нужен |
| --- | --- | --- |
| `fastapi` | FastAPI, Uvicorn | HTTP endpoint для callback-ов кнопок |
| `websocket` | websockets | Получение событий Mattermost в реальном времени |
| `redis` | redis | Хранение состояний и данных пользователей |
| `all` | Все зависимости выше | Полная установка |

Для обычного бота с FastAPI и WebSocket:

```bash
pip install "aiomost-tools[fastapi,websocket] @ git+https://github.com/IliaPr/aiomost.git"
```

Для проекта с Redis-хранилищем состояний:

```bash
pip install "aiomost-tools[fastapi,websocket,redis] @ git+https://github.com/IliaPr/aiomost.git"
```

Чтобы установить все интеграции:

```bash
pip install "aiomost-tools[all] @ git+https://github.com/IliaPr/aiomost.git"
```

!!! tip
    Устанавливайте только нужные extras. Например, для отправки сообщений через
    `MMBot` достаточно базовой установки.

## Проверка установки

```bash
python -c "import aiomost; print(aiomost.__version__)"
```

Команда должна вывести установленную версию библиотеки без ошибок импорта.

## Следующий шаг

После установки нужно передать URL Mattermost и токен бота. Это будет описано
в разделе «Конфигурация».
