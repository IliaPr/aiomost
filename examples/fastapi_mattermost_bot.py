from aiomost import MattermostBotApp


bot_app = MattermostBotApp.from_env()


@bot_app.message()
async def handle_posted(event, bot, app):
    post = event.data.post
    message = (post.message or "").strip()

    if message == "!ping":
        await bot.reply_message(
            channel_id=post.channel_id,
            message_id=post.id,
            text="pong",
            actions=app.actions([("ping_ok", "OK", "ping_ok")]),
        )


@bot_app.button("ping_ok")
async def handle_ping_button(event):
    return {
        "update": {
            "message": "Button received",
        }
    }


app = bot_app.create_fastapi_app()
