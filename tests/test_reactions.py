import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

from aiomost import MMBot, MattermostBotApp, Reaction, ReactionEvent


REACTION_PAYLOAD = {
    "user_id": "user-id",
    "post_id": "post-id",
    "emoji_name": "thumbsup",
    "create_at": 1710000000000,
}


class ReactionApiTest(unittest.TestCase):
    def setUp(self):
        self.bot = MMBot("https://mattermost.example.com", "token")

    def _response(self, payload):
        response = Mock()
        response.json.return_value = payload
        return response

    def test_add_reaction_sends_api_v4_payload(self):
        self.bot.send_request = AsyncMock(
            return_value=self._response(REACTION_PAYLOAD)
        )

        reaction = asyncio.run(
            self.bot.add_reaction("post-id", "thumbsup", user_id="user-id")
        )

        self.bot.send_request.assert_awaited_once_with(
            "api/v4/reactions",
            "POST",
            json_data={
                "user_id": "user-id",
                "post_id": "post-id",
                "emoji_name": "thumbsup",
            },
        )
        self.assertIsInstance(reaction, Reaction)
        self.assertEqual(reaction.emoji_name, "thumbsup")

    def test_get_reactions_returns_models(self):
        self.bot.send_request = AsyncMock(
            return_value=self._response([REACTION_PAYLOAD])
        )

        reactions = asyncio.run(self.bot.get_reactions("post/id"))

        self.bot.send_request.assert_awaited_once_with(
            "api/v4/posts/post%2Fid/reactions",
            "GET",
        )
        self.assertEqual(len(reactions), 1)
        self.assertIsInstance(reactions[0], Reaction)

    def test_remove_reaction_encodes_path_values(self):
        self.bot.send_request = AsyncMock(
            return_value=self._response({"status": "OK"})
        )

        result = asyncio.run(
            self.bot.remove_reaction("post/id", "+1", user_id="user/id")
        )

        self.bot.send_request.assert_awaited_once_with(
            "api/v4/users/user%2Fid/posts/post%2Fid/reactions/%2B1",
            "DELETE",
        )
        self.assertEqual(result, {"status": "OK"})


class ReactionEventTest(unittest.TestCase):
    def test_reaction_event_parses_json_encoded_reaction(self):
        event = ReactionEvent(
            event="reaction_added",
            data={
                "reaction": (
                    '{"user_id":"user-id","post_id":"post-id",'
                    '"emoji_name":"thumbsup","create_at":1710000000000}'
                )
            },
            broadcast={"channel_id": "channel-id"},
            seq=4,
        )

        self.assertEqual(event.event_type, "reaction_added")
        self.assertIsInstance(event.data.reaction, Reaction)
        self.assertEqual(event.data.reaction.post_id, "post-id")
        self.assertEqual(event.broadcast.channel_id, "channel-id")

    def test_reaction_added_decorator_dispatches_event(self):
        app = MattermostBotApp("https://mattermost.example.com", "token")
        handled = []

        @app.reaction_added()
        async def handle_reaction(event):
            handled.append(event.data.reaction.emoji_name)

        event = ReactionEvent(
            event="reaction_added",
            data={"reaction": REACTION_PAYLOAD},
        )
        asyncio.run(app.dispatch(event.event_type, event))

        self.assertEqual(handled, ["thumbsup"])

    def test_reaction_removed_decorator_dispatches_event(self):
        app = MattermostBotApp("https://mattermost.example.com", "token")
        handled = []

        @app.reaction_removed()
        async def handle_reaction(event):
            handled.append(event.data.reaction.post_id)

        event = ReactionEvent(
            event="reaction_removed",
            data={"reaction": REACTION_PAYLOAD},
        )
        asyncio.run(app.dispatch(event.event_type, event))

        self.assertEqual(handled, ["post-id"])


if __name__ == "__main__":
    unittest.main()
