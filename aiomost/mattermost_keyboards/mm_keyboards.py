import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def generate_actions(base_url: str, buttons: List[tuple], action_path: str = "/mattermost/action") -> List[Dict]:
    """
    Генерирует JSON с кнопками для интеграции Mattermost.

    :param base_url: Базовый URL для интеграции.
    :param buttons: Список кнопок, где каждая - это (id, name, action).
    :return: JSON-объект со списком кнопок.
    """
    callback_url = f"{base_url.rstrip('/')}/{action_path.strip('/')}"

    actions = [
        {
            "id": button_id,
            "name": button_name,
            "integration": {
                "url": callback_url,
                "context": {
                    "action": action
                }
            }
        }
        for button_id, button_name, action in buttons
    ]

    logger.debug(f"Generated actions: {actions}")

    return actions
