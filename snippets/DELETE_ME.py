# TODO: Delete me

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

from config import BOT_TOKEN
CHANNEL_ID = -1002096051693

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

async def is_user_subscribed(user_id: int, channel_id: int) -> bool:
    """
    Проверка, состоит ли пользователь в канале (статус MEMBER, ADMIN, OWNER)
    """
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ('member', 'administrator', 'creator')
    except Exception as e:
        logging.warning(f"Ошибка проверки подписки: {e}")
        return False

@dp.message(Command("check"))
async def check_subscription(message: Message):
    user_id = message.from_user.id
    # Если используешь username, можно CHANNEL_ID = "@my_channel"
    subscribed = await is_user_subscribed(user_id, CHANNEL_ID)
    if subscribed:
        await message.answer("✅ Вы подписаны на канал!")
    else:
        # Формируем ссылку на канал
        if str(CHANNEL_ID).startswith("-100"):
            # Если chat_id, то нужно иметь username для красивой ссылки
            channel_link = "https://t.me/your_channel_username"  # Замени!
        else:
            channel_link = f"https://t.me/{CHANNEL_ID.lstrip('@')}"
        await message.answer(
            f"🚫 Для доступа подпишитесь на наш канал: <a href='{channel_link}'>Перейти в канал</a>",
            disable_web_page_preview=True
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
