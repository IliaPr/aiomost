import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from aiomost.mattermost_actions.mm_actions import MMBot
from aiomost.mattermost_dispatcher.dispatcher import Dispatcher
from aiomost.mattermost_keyboards.mm_keyboards import generate_actions
from aiomost.mattermost_models.button_query.button_query_model import (
    MattermostButtonQuery,
)
from aiomost.mattermost_routers.mm_routers import Router
from aiomost.mattermost_state_storage.matter_states import State

ButtonData = Union[str, Callable[[str], bool]]
ButtonSpec = Tuple[str, str, str]


class MattermostBotApp:
    """
    High-level Mattermost bot application.

    It wires together the HTTP client, router, dispatcher, optional Redis state,
    FastAPI button callback endpoint, and websocket event listener.
    """

    def __init__(
        self,
        mattermost_url: str,
        bot_token: str,
        *,
        public_base_url: Optional[str] = None,
        websocket_url: Optional[str] = None,
        state_manager: Any = None,
        redis_url: Optional[str] = None,
        router: Optional[Router] = None,
        dispatcher: Optional[Dispatcher] = None,
        ignore_bot_messages: bool = True,
    ) -> None:
        if state_manager and redis_url:
            raise ValueError("Use either state_manager or redis_url, not both")

        if redis_url:
            from aiomost.mattermost_state_storage.redis_state_manager import (
                RedisStateManager,
            )

            state_manager = RedisStateManager.from_url(redis_url)

        self.mattermost_url = mattermost_url.rstrip("/")
        self.bot_token = bot_token
        self.public_base_url = public_base_url.rstrip("/") if public_base_url else None
        self.websocket_url = websocket_url or self._build_websocket_url(self.mattermost_url)
        self.ignore_bot_messages = ignore_bot_messages

        self.bot = MMBot(self.mattermost_url, self.bot_token)
        self.router = router or Router(name="mattermost", state_manager=state_manager)
        self.dispatcher = dispatcher or Dispatcher(state_manager=state_manager)

        if self.router not in self.dispatcher.routers:
            self.dispatcher.include_router(self.router)

    @classmethod
    def from_env(
        cls,
        *,
        mattermost_url_env: str = "MATTERMOST_URL",
        bot_token_env: str = "MATTERMOST_BOT_TOKEN",
        websocket_url_env: str = "MATTERMOST_WS_URL",
        public_base_url_env: str = "PUBLIC_BASE_URL",
        redis_url_env: str = "REDIS_URL",
    ) -> "MattermostBotApp":
        mattermost_url = cls._require_env(mattermost_url_env)
        bot_token = cls._require_env(bot_token_env)
        return cls(
            mattermost_url=mattermost_url,
            bot_token=bot_token,
            websocket_url=os.getenv(websocket_url_env),
            public_base_url=os.getenv(public_base_url_env),
            redis_url=os.getenv(redis_url_env),
        )

    @staticmethod
    def _require_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"{name} environment variable is required")
        return value

    @staticmethod
    def _build_websocket_url(mattermost_url: str) -> str:
        base = mattermost_url.rstrip("/")
        if base.startswith("https://"):
            base = "wss://" + base.removeprefix("https://")
        elif base.startswith("http://"):
            base = "ws://" + base.removeprefix("http://")
        return f"{base}/api/v4/websocket"

    def message(
        self,
        *filters: Callable,
        required_state: Optional[State] = None,
    ) -> Callable:
        return self.router.posted(*filters, required_state=required_state)

    def user_added(self, *filters: Callable) -> Callable:
        return self.router.user_added(*filters)

    def error(self, *filters: Callable) -> Callable:
        return self.router.errors(*filters)

    def event(self, event_name: str, *filters: Callable) -> Callable:
        observer = self.router.observers.get(event_name)
        if observer is None:
            raise ValueError(f"Unsupported Mattermost event: {event_name}")
        return observer(*filters)

    def button(
        self,
        action: Optional[ButtonData] = None,
        *,
        required_state: Optional[State] = None,
    ) -> Callable:
        return self.router.button_query(
            button_data=action,
            required_state=required_state,
        )

    on_message = message
    on_user_added = user_added
    on_error = error
    on_event = event
    on_button = button

    def actions(
        self,
        buttons: List[ButtonSpec],
        *,
        base_url: Optional[str] = None,
        action_path: str = "/mattermost/action",
    ) -> List[Dict[str, Any]]:
        target_base_url = (base_url or self.public_base_url or "").rstrip("/")
        if not target_base_url:
            raise RuntimeError("public_base_url or base_url is required for buttons")
        return generate_actions(target_base_url, buttons, action_path=action_path)

    async def setup(self) -> None:
        if not self.ignore_bot_messages:
            return
        self.router.bot_user_id = await self.bot.get_bot_user_id()

    async def dispatch(self, update_type: str, event: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("bot", self.bot)
        kwargs.setdefault("app", self)
        return await self.dispatcher.dispatch(update_type, event, **kwargs)

    async def handle_button_payload(self, data: Dict[str, Any]) -> Any:
        event = MattermostButtonQuery(data)
        response = await self.dispatch("button_query", event)
        return response if response is not None else {
            "event_type": "button_query",
            "data": data,
        }

    async def run_websocket_forever(self) -> None:
        from aiomost.mattermost_websockets.mm_websockets import mattermost_ws_listener

        await mattermost_ws_listener(
            [self.router],
            self.websocket_url,
            self.bot_token,
            bot=self.bot,
            app=self,
        )

    def create_fastapi_app(
        self,
        *,
        title: str = "aiomost Mattermost bot",
        action_path: str = "/mattermost/action",
        include_healthcheck: bool = True,
    ):
        from fastapi import FastAPI, Request

        normalized_action_path = "/" + action_path.strip("/")

        @asynccontextmanager
        async def lifespan(app):
            await self.setup()
            ws_task = asyncio.create_task(self.run_websocket_forever())
            try:
                yield
            finally:
                ws_task.cancel()
                try:
                    await ws_task
                except asyncio.CancelledError:
                    pass

        fastapi_app = FastAPI(title=title, lifespan=lifespan)

        if include_healthcheck:
            @fastapi_app.get("/health")
            async def health():
                return {"status": "ok"}

        @fastapi_app.post(normalized_action_path)
        async def handle_mattermost_action(request: Request):
            return await self.handle_button_payload(await request.json())

        return fastapi_app
