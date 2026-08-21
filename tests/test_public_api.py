import asyncio
import os
import ssl
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiomost import (
    Dispatcher,
    MMBot,
    Mattermost,
    MattermostBotApp,
    Reaction,
    ReactionEvent,
    Router,
    State,
    StatesGroup,
)
from aiomost.mattermost_websockets.mm_websockets import _create_ssl_context


class PublicApiTest(unittest.TestCase):
    def test_public_api_imports(self):
        self.assertTrue(Dispatcher)
        self.assertTrue(MMBot)
        self.assertTrue(Mattermost)
        self.assertTrue(MattermostBotApp)
        self.assertTrue(Reaction)
        self.assertTrue(ReactionEvent)
        self.assertTrue(Router)
        self.assertTrue(State)
        self.assertTrue(StatesGroup)

    def test_mattermost_url_is_normalized(self):
        bot = MMBot("https://mattermost.example.com/", "token")

        self.assertEqual(bot.api_url, "https://mattermost.example.com")

    def test_router_has_no_hardcoded_bot_user_id(self):
        router = Router()

        self.assertIsNone(router.bot_user_id)

    def test_mattermost_bot_app_builds_actions(self):
        app = MattermostBotApp(
            "https://mattermost.example.com",
            "token",
            public_base_url="https://bot.example.com/",
        )

        actions = app.actions([("ok", "OK", "ok")])

        self.assertEqual(
            actions[0]["integration"]["url"],
            "https://bot.example.com/mattermost/action",
        )

    def test_handler_can_accept_only_event(self):
        app = MattermostBotApp("https://mattermost.example.com", "token")
        handled = []

        @app.message()
        async def message(event):
            handled.append(event)

        event = SimpleNamespace(
            event_type="posted",
            data=SimpleNamespace(
                post=SimpleNamespace(user_id="user", message="hello"),
            ),
        )

        asyncio.run(app.dispatch("posted", event))

        self.assertEqual(handled, [event])

    def test_button_payload_dispatches_to_registered_handler(self):
        app = MattermostBotApp("https://mattermost.example.com", "token")

        @app.button("confirm")
        async def confirm(event):
            return {"update": {"message": event.action}}

        response = asyncio.run(
            app.handle_button_payload(
                {
                    "context": {"action": "confirm"},
                    "user_id": "user",
                    "channel_id": "channel",
                }
            )
        )

        self.assertEqual(response, {"update": {"message": "confirm"}})

    def test_websocket_tls_verification_is_enabled_by_default(self):
        context = _create_ssl_context("wss://mattermost.example.com/websocket", True)

        self.assertIsNotNone(context)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_websocket_tls_verification_can_be_disabled_explicitly(self):
        context = _create_ssl_context("wss://localhost/websocket", False)

        self.assertIsNotNone(context)
        self.assertFalse(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)

    def test_plain_websocket_does_not_use_ssl_context(self):
        self.assertIsNone(_create_ssl_context("ws://localhost/websocket", True))

    def test_verify_ssl_can_be_configured_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "MATTERMOST_URL": "https://mattermost.example.com",
                "MATTERMOST_BOT_TOKEN": "token",
                "MATTERMOST_VERIFY_SSL": "false",
            },
            clear=True,
        ):
            app = MattermostBotApp.from_env()

        self.assertFalse(app.verify_ssl)

    def test_websocket_listener_receives_verify_ssl_setting(self):
        app = MattermostBotApp(
            "https://mattermost.example.com",
            "token",
            verify_ssl=False,
        )

        listener = AsyncMock()
        with patch(
            "aiomost.mattermost_websockets.mm_websockets.mattermost_ws_listener",
            listener,
        ):
            asyncio.run(app.run_websocket_forever())

        listener.assert_awaited_once_with(
            [app.router],
            app.websocket_url,
            app.bot_token,
            verify_ssl=False,
            bot=app.bot,
            app=app,
        )


if __name__ == "__main__":
    unittest.main()
