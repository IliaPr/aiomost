import json
from typing import Any, Dict, Optional

from aiomost.mattermost_models.base_model.base_model import BaseModel


class Reaction(BaseModel):
    """An emoji reaction returned by the Mattermost API v4."""

    def __init__(
        self,
        user_id: str,
        post_id: str,
        emoji_name: str,
        create_at: int = 0,
        **kwargs: Any,
    ) -> None:
        self.user_id = user_id
        self.post_id = post_id
        self.emoji_name = emoji_name
        self.create_at = create_at

        for key, value in kwargs.items():
            setattr(self, key, value)


class ReactionData(BaseModel):
    """Payload of a ``reaction_added`` or ``reaction_removed`` event."""

    def __init__(self, reaction: Any, **kwargs: Any) -> None:
        if isinstance(reaction, str):
            reaction = json.loads(reaction)
        self.reaction = Reaction(**reaction) if isinstance(reaction, dict) else reaction

        for key, value in kwargs.items():
            setattr(self, key, value)


class ReactionEvent(BaseModel):
    """Mattermost WebSocket event carrying a reaction."""

    def __init__(
        self,
        event: str,
        data: Dict[str, Any],
        broadcast: Optional[Dict[str, Any]] = None,
        seq: int = 0,
        **kwargs: Any,
    ) -> None:
        self.event = event
        self.data = ReactionData(**data) if isinstance(data, dict) else data
        self.broadcast = BaseModel(**broadcast) if isinstance(broadcast, dict) else broadcast
        self.seq = seq

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def event_type(self) -> str:
        return self.event
