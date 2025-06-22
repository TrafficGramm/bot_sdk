import datetime
from unittest.mock import AsyncMock
from aiogram.types import Message, User, Chat
from aiogram import Bot

def make_fake_message(user_id: int, text: str = "/start") -> Message:
    message = Message.model_construct(
        message_id=123,
        date=datetime.datetime.now(datetime.timezone.utc),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        chat=Chat(id=user_id, type="private"),
        text=text
    )
    message._bot = AsyncMock(spec=Bot) # type: ignore
    return message
