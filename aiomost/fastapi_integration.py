import inspect
from typing import Any, Callable, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, model_validator

from aiomost.mattermost_actions.mm_actions import MMBot
from aiomost.mattermost_dispatcher.dispatcher import Dispatcher
from aiomost.mattermost_models.base_model.base_model import BaseModel as AiomostBaseModel
from aiomost.mattermost_models.button_query.button_query_model import (
    MattermostButtonQuery,
)


class MessageRequest(BaseModel):
    channel_id: Optional[str] = Field(
        None, description="Mattermost channel ID for channel messages"
    )
    user_id: Optional[str] = Field(
        None, description="Mattermost user ID for direct messages"
    )
    text: str = Field(..., min_length=1, description="Message text")
    actions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Mattermost interactive message actions"
    )
    root_id: Optional[str] = Field(
        None, description="Root post ID when replying in a thread"
    )
    file_ids: Optional[List[str]] = Field(
        None, description="Already uploaded Mattermost file IDs"
    )
    bot_token: Optional[str] = Field(
        None, description="Optional override token for this request"
    )

    @model_validator(mode="after")
    def validate_target(self) -> "MessageRequest":
        if bool(self.channel_id) == bool(self.user_id):
            raise ValueError("Provide exactly one of channel_id or user_id")
        if self.root_id and not self.channel_id:
            raise ValueError("root_id can only be used with channel_id")
        return self


class MessageResponse(BaseModel):
    status: str = "ok"
    id: Optional[str] = None
    channel_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class BotCallRequest(BaseModel):
    method: str = Field(..., min_length=1, description="MMBot method name")
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    bot_token: Optional[str] = Field(
        None, description="Optional override token for this request"
    )


class BotCallResponse(BaseModel):
    status: str = "ok"
    result: Optional[Any] = None


def normalize_result(value: Any) -> Any:
    if isinstance(value, httpx.Response):
        try:
            data = value.json()
        except ValueError:
            data = value.text
        return {"status_code": value.status_code, "data": data}
    if isinstance(value, AiomostBaseModel):
        return normalize_result(value.__dict__)
    if isinstance(value, dict):
        return {key: normalize_result(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_result(item) for item in value]
    return value


def create_mattermost_api_router(
    mattermost_url: str,
    bot_token: str,
    dispatcher: Optional[Dispatcher] = None,
    auth_dependency: Optional[Callable[..., Any]] = None,
    prefix: str = "/api/mattermost",
    tags: Optional[List[str]] = None,
) -> APIRouter:
    dependencies = [Depends(auth_dependency)] if auth_dependency else None
    router = APIRouter(
        prefix=prefix,
        tags=tags or ["Mattermost"],
        dependencies=dependencies,
    )
    mm_bot = MMBot(mattermost_url, bot_token)
    dp = dispatcher or Dispatcher()
    allowed_bot_methods = {
        name
        for name, member in inspect.getmembers(MMBot, predicate=callable)
        if not name.startswith("_") and name not in {"send_request"}
    }

    @router.post("/messages", response_model=MessageResponse)
    async def send_message(payload: MessageRequest) -> MessageResponse:
        try:
            bot = mm_bot if not payload.bot_token else MMBot(
                mattermost_url, payload.bot_token
            )
            if payload.user_id:
                data = await bot.send_direct_message(
                    user_id=payload.user_id,
                    text=payload.text,
                    actions=payload.actions,
                )
            elif payload.file_ids:
                data = await bot.send_message_with_files(
                    channel_id=payload.channel_id,
                    text=payload.text,
                    file_ids=payload.file_ids,
                )
            elif payload.root_id:
                data = await bot.reply_message(
                    channel_id=payload.channel_id,
                    message_id=payload.root_id,
                    text=payload.text,
                    actions=payload.actions,
                )
            else:
                data = await bot.send_message(
                    channel_id=payload.channel_id,
                    text=payload.text,
                    actions=payload.actions,
                )

            return MessageResponse(
                id=data.get("id") if isinstance(data, dict) else None,
                channel_id=data.get("channel_id")
                if isinstance(data, dict)
                else payload.channel_id,
                raw=data if isinstance(data, dict) else None,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not send Mattermost message: {exc}",
            ) from exc

    @router.post("/bot/call", response_model=BotCallResponse)
    async def call_bot_method(payload: BotCallRequest) -> BotCallResponse:
        if payload.method not in allowed_bot_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Method is not available: {payload.method}",
            )

        bot = mm_bot if not payload.bot_token else MMBot(mattermost_url, payload.bot_token)
        target = getattr(bot, payload.method, None)
        if not callable(target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Method not found: {payload.method}",
            )

        try:
            result = await target(*payload.args, **payload.kwargs)
        except TypeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid method arguments: {exc}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Method call failed: {exc}",
            ) from exc

        return BotCallResponse(result=jsonable_encoder(normalize_result(result)))

    @router.post("/action")
    async def handle_button_action(request: Request):
        data = await request.json()
        event = MattermostButtonQuery(data)
        response = await dp.dispatch("button_query", event)
        return response if response is not None else {
            "event_type": "button_query",
            "data": data,
        }

    return router
