from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict


def get_channels_keyboard(channels: Dict[str, str], max_channels: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, url=url)]
        for name, url in list(channels.items())[:max_channels]
    ]
    buttons.append([InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
