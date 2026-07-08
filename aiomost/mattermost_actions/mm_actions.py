import mimetypes
from typing import Dict, List, Optional
import httpx

from aiomost.mattermost_models.user.user_info.user_info_models import User


class Mattermost:
    def __init__(self, api_url: str, bot_token: str):
        self.api_url = api_url.rstrip("/")
        self.bot_token = bot_token
        self.headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

    async def send_request(self, endpoint: str, method: str = 'POST', json_data: Optional[Dict] = None, files: Optional[Dict] = None):
        headers = self.headers.copy()  # Создаем копию заголовков
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        if files:  # Если загружаем файлы, убираем Content-Type, т.к. httpx сам добавит нужный
            headers.pop("Content-Type", None)

        async with httpx.AsyncClient() as client:
            if method.upper() == 'POST':
                response = await client.post(
                    url,
                    headers=headers,
                    json=json_data if not files else None,
                    files=files
                )
            elif method.upper() == 'PUT':
                response = await client.put(url, headers=headers, json=json_data)
            elif method.upper() == 'DELETE':
                response = await client.delete(url, headers=headers)
            else:
                response = await client.get(
                    url,
                    headers=headers
                )

        if response.status_code < 200 or response.status_code >= 300:
            response.raise_for_status()
        return response


class MMBot(Mattermost):
    async def reply_message(self, channel_id: str, message_id: str, text: str, actions: Optional[List[Dict]] = None):
        message = {
            "channel_id": channel_id,
            "message": text,
            "root_id": message_id,
            "props": {}
        }

        # Добавляем кнопки только если они переданы
        if actions:
            message["props"]["attachments"] = [{"actions": actions}]

        response = await self.send_request('api/v4/posts', 'POST', json_data=message)

        if response.status_code == 201:
            pass
            # print("✅ Сообщение отправлено успешно!")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
        return response.json()

    async def send_message_with_files(self, channel_id: str, text: str, file_ids: List[str]):
        file_ids_uploaded = []

        async with httpx.AsyncClient() as client:
            for file_id in file_ids:
                # Загружаем файл с сервера Mattermost
                file_response = await client.get(
                    f"{self.api_url}/api/v4/files/{file_id}",
                    headers={"Authorization": f"Bearer {self.bot_token}"}
                )

                if file_response.status_code != 200:
                    print(f"❌ Ошибка при загрузке файла с ID {file_id}")
                    continue

                file_content = file_response.content
                content_type = file_response.headers.get(
                    "Content-Type", "application/octet-stream")
                extension = mimetypes.guess_extension(content_type) or ""

                # Загружаем файл в Mattermost
                files = {
                    "files": (f"downloaded_file{extension}", file_content, content_type),
                }
                data = {"channel_id": channel_id}

                upload_response = await client.post(
                    f"{self.api_url}/api/v4/files",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    files=files,
                    data=data  # В `httpx` канал передается через `data`, а не в `files`
                )

                if upload_response.status_code != 201:
                    print(
                        f"❌ Ошибка при загрузке файла с ID {file_id} в Mattermost")
                    continue

                upload_json = upload_response.json()
                new_file_id = upload_json["file_infos"][0]["id"]
                file_ids_uploaded.append(new_file_id)

            # Если файлы были успешно загружены, отправляем сообщение
            if file_ids_uploaded:
                post_data = {
                    "channel_id": channel_id,
                    "message": text,
                    "file_ids": file_ids_uploaded
                }

                post_response = await client.post(
                    f"{self.api_url}/api/v4/posts",
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json"
                    },
                    json=post_data
                )

                if post_response.status_code == 201:
                    pass
                    # print("✅ Сообщение с файлами успешно отправлено")
                else:
                    error_msg = f"Ошибка при отправке сообщения: {post_response.status_code}"
                    if post_response.status_code == 403:
                        error_msg += " (нет доступа к каналу)"
                    elif post_response.status_code == 404:
                        error_msg += " (канал не найден)"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)

                return post_response.json()

            else:
                error_msg = "Не удалось загрузить файлы"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)

    async def send_message(self, channel_id: str, text: str, actions: Optional[List[Dict]] = None):
        """
        Отправляет сообщение в Mattermost с возможностью добавления кнопок.
        """
        message = {
            "channel_id": channel_id,
            "message": text,
            "props": {}
        }

        # Добавляем кнопки только если они переданы
        if actions:
            message["props"]["attachments"] = [{"actions": actions}]

        # print("📩 Отправка сообщения:", message)  # Логируем перед отправкой

        response = await self.send_request('api/v4/posts', 'POST', json_data=message)

        if response.status_code == 201:
            pass
            # print("✅ Сообщение отправлено успешно!")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")

        return response.json()  # Возвращаем ответ API (может быть полезно)

    async def update_notification_settings(self, user_id: str):
        """
        Обновляет настройки уведомлений пользователя.
        """
        endpoint = f"api/v4/users/{user_id}/patch"
        data = {
            "user_id": user_id,
            "notify_props": {
                "desktop": "all",  # Уведомления на рабочем столе для всех сообщений
                "desktop_sound": "true",  # Включение звука уведомлений на рабочем столе
                "push": "all",  # Уведомления push для всех сообщений
                "push_status": "online"  # Уведомления только если пользователь онлайн
            }
        }

        response = await self.send_request(endpoint, 'PUT', json_data=data)
        # print(f"✅ Настройки уведомлений обновлены для {user_id}: {response}")
        return response

    async def edit_message(self, message_id: str, text: str, actions: Optional[List[Dict]] = None):
        """
        Редактирует сообщение в Mattermost.
        """
        message = {
            "id": message_id,
            "message": text,
            "props": {}
        }

        # Добавляем кнопки только если они переданы
        if actions:
            message["props"]["attachments"] = [{"actions": actions}]

        response = await self.send_request(
            f'api/v4/posts/{message_id}', 'PUT', json_data=message)

        if response.status_code == 200:
            print("✅ Сообщение успешно отредактировано!")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")

    async def get_files_by_ids(self, file_ids: List[str]):
        """ Получает файлы из Mattermost по их ID и возвращает список их данных. """
        files_data = []

        async with httpx.AsyncClient() as client:
            for file_id in file_ids:
                file_response = await client.get(
                    f"{self.api_url}/api/v4/files/{file_id}",
                    headers={"Authorization": f"Bearer {self.bot_token}"}
                )

                if file_response.status_code != 200:
                    print(f"❌ Ошибка при загрузке файла с ID {file_id}")
                    continue

                file_content = file_response.content
                content_type = file_response.headers.get(
                    "Content-Type", "application/octet-stream")
                extension = mimetypes.guess_extension(content_type) or ".bin"
                filename = f"{file_id}{extension}"

                files_data.append({
                    "filename": filename,
                    "content": file_content,
                    "content_type": content_type
                })

        return files_data  # Список загруженных файлов

    async def get_user_info(self, user_id: str) -> Optional[User]:
        """
        Получает информацию о пользователе по user_id и возвращает объект User.
        """
        endpoint = f"api/v4/users/{user_id}"
        response = await self.send_request(endpoint, 'GET')

        if response.status_code == 200:
            return User(**response.json())  # Конвертируем JSON в объект User
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return None  # Возвращаем None при ошибке

    async def set_user_avatar(self, user_id: str, avatar_url: str):
        """
        Загружает аватар по ссылке и устанавливает его в качестве аватара пользователя в Mattermost.
        :param user_id: ID пользователя в Mattermost
        :param avatar_url: Ссылка на изображение Bitrix24
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(avatar_url)
            if response.status_code != 200:
                print(f"❌ Ошибка загрузки аватара: {response.status_code}")
                return False

            image_bytes = response.content
            content_type = response.headers.get(
                "Content-Type", "application/octet-stream")
            extension = mimetypes.guess_extension(content_type) or ".jpg"

        files = {
            "image": (f"avatar{extension}", image_bytes, content_type),
        }

        upload_response = await self.send_request(
            f"api/v4/users/{user_id}/image", "POST", files=files
        )

        if upload_response.status_code == 200:
            print("✅ Аватар успешно обновлен в Mattermost!")
            return True
        else:
            print(
                f"❌ Ошибка при обновлении аватара: {upload_response.text}")
            return False

    async def get_bot_user_id(self) -> Optional[str]:
        """
        Получает ID бота по его токену.
        """
        response = await self.send_request('api/v4/users/me', 'GET')

        if response.status_code == 200:
            return response.json().get("id")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return None

    async def send_direct_message(self, user_id: str, text: str, actions: Optional[List[Dict]] = None):
        """
        Отправляет личное сообщение пользователю в Mattermost.
        :param user_id: ID пользователя, которому отправляется сообщение.
        :param text: Текст сообщения.
        :param actions: (Опционально) Кнопки (действия) в сообщении.
        """
        # Получаем ID бота
        bot_user_id = await self.get_bot_user_id()
        if not bot_user_id:
            print("❌ Ошибка: не удалось получить ID бота")
            return None

        # Создаём DM-канал
        response = await self.send_request(
            'api/v4/channels/direct', 'POST', json_data=[bot_user_id, user_id]
        )

        if response.status_code != 201:
            print(
                f"❌ Ошибка при создании DM-канала: {response.status_code} {response.text}")
            return None

        channel_id = response.json().get("id")

        # Формируем сообщение
        message = {
            "channel_id": channel_id,
            "message": text,
            "props": {}
        }

        if actions:
            message["props"]["attachments"] = [{"actions": actions}]

        # Отправляем сообщение
        response = await self.send_request('api/v4/posts', 'POST', json_data=message)

        if response.status_code == 201:
            print("✅ Личное сообщение отправлено успешно!")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")

        return response.json()  # Возвращаем JSON-ответ от API

    async def delete_message(self, message_id: str) -> Optional[str]:
        """
        Удаляет сообщение по его ID.
        """
        response = await self.send_request(f'api/v4/posts/{message_id}', 'DELETE')

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return None

    async def is_channel_admin(self, user_id: str, channel_id: str) -> bool:
        """
        Проверяет, является ли пользователь администратором канала в Mattermost.
        :param user_id: ID пользователя
        :param channel_id: ID канала
        :return: True, если пользователь - администратор, иначе False
        """
        endpoint = f"api/v4/channels/{channel_id}/members/{user_id}"
        response = await self.send_request(endpoint, 'GET')

        if response.status_code == 200:
            roles = response.json().get("roles", "")
            return "channel_admin" in roles.split()
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return False

    async def send_ephemeral_message(self, user_id: str, channel_id: str, text: str):
        """
        Отправляет эфемерное (временное) сообщение пользователю в канале.
        :param user_id: ID пользователя, которому отправляется сообщение.
        :param channel_id: ID канала, в котором отображается сообщение.
        :param text: Текст сообщения.
        """
        message = {
            "user_id": user_id,
            "post": {
                "channel_id": channel_id,
                "message": text
            }
        }

        response = await self.send_request('api/v4/posts/ephemeral', 'POST', json_data=message)

        if response.status_code == 201:
            pass
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")

    async def update_user_info(self, user_id: str, data: Dict):
        """
        Обновляет информацию о пользователе в Mattermost.
        :param user_id: ID пользователя
        :param data: Словарь с данными для обновления
        """
        endpoint = f"api/v4/users/{user_id}/patch"
        response = await self.send_request(endpoint, 'PUT', json_data=data)

        if response.status_code == 200:
            pass
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Получает информацию о пользователе по его username и возвращает объект User.
        :param username: Имя пользователя в Mattermost.
        :return: Объект User или None, если пользователь не найден.
        """
        endpoint = f"api/v4/users/username/{username}"
        response = await self.send_request(endpoint, 'GET')

        if response.status_code == 200:
            return User(**response.json())  # Конвертируем JSON в объект User
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return None

    async def remove_user_from_team(self, user_id: str, team_id: str) -> bool:
        """
        Удаляет пользователя из команды.
        :param user_id: ID пользователя
        :param team_id: ID команды
        :return: True, если пользователь успешно удален, иначе False
        """
        endpoint = f"api/v4/teams/{team_id}/members/{user_id}"
        response = await self.send_request(endpoint, 'DELETE')

        if response.status_code == 200:
            return True
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return False

    async def follow_thread(self, user_id: str, team_id: str, thread_id: str) -> bool:
        """
        Подписывает пользователя на тред (ветку сообщений) в Mattermost.
        :param user_id: ID пользователя, которого нужно подписать
        :param team_id: ID команды
        :param thread_id: ID треда (root post ID)
        :return: True если успешно, False если ошибка
        """
        endpoint = f"api/v4/users/{user_id}/teams/{team_id}/threads/{thread_id}/following"
        try:
            response = await self.send_request(endpoint, 'PUT')
            if response.status_code == 200:
                return True
            else:
                print(
                    f"❌ Ошибка подписки на тред {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Исключение при подписке на тред: {e}")
            return False

    async def mark_thread_as_unread(self, user_id: str, team_id: str, thread_id: str, timestamp: int = None) -> bool:
        """
        Помечает тред как непрочитанный для пользователя.
        :param user_id: ID пользователя
        :param team_id: ID команды
        :param thread_id: ID треда (root post ID)
        :param timestamp: Временная метка сообщения (в миллисекундах). Если None, используется текущее время.
        :return: True если успешно, False если ошибка
        """
        endpoint = f"api/v4/users/{user_id}/teams/{team_id}/threads/{thread_id}/set_unread/{thread_id}"
        try:
            response = await self.send_request(endpoint, 'POST')
            if response.status_code == 200:
                return True
            else:
                print(
                    f"❌ Ошибка пометки треда как непрочитанного {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Исключение при пометке треда как непрочитанного: {e}")
            return False
