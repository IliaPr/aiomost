import asyncio
import unittest
from types import SimpleNamespace

from aiomost import Dispatcher, MMBot, Mattermost, MattermostBotApp, Router, State, StatesGroup


class PublicApiTest(unittest.TestCase):
    def test_public_api_imports(self):
        self.assertTrue(Dispatcher)
        self.assertTrue(MMBot)
        self.assertTrue(Mattermost)
        self.assertTrue(MattermostBotApp)
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


if __name__ == "__main__":
    unittest.main()
