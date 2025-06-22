import aiohttp
from typing import cast
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto,
    InputMediaVideo, MediaUnion, Message
)

from sdk.types import Ad

class AdService:
    def __init__(self, channels_api_url: str, check_api_url: str):
        self.channels_api_url = channels_api_url
        self.check_api_url = check_api_url


    async def fetch_ad(self, user_id: int) -> list[Ad]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.channels_api_url, params={"user_id": user_id}) as resp:
                    ads = cast(list[Ad], await resp.json())
                    return ads
            except Exception as e:
                print(f"[ERROR] Ошибка при получении рекламы: {e}")
                return []

    async def is_user_subscribed(self, user_id: int, channel_url: str) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                print(self.check_api_url)
                async with session.post(self.check_api_url, json={"user_id": user_id, "channel_url": channel_url}) as resp:
                    result = await resp.json()
                    return result.get("subscribed", False)
            except Exception as e:
                print(f"[ERROR] Ошибка при проверке подписки: {e}")
                return False

    async def handle_h_ad(self, event: Message, ad: Ad):
        media_raw: str | list[str] = ad.get("media", [])
        media: list[str] = [media_raw] if isinstance(media_raw, str) else media_raw or []
        
        media_type = ad.get("media_type", "photo")
        text = ad.get("text", "")
        buttons = ad.get("buttons", [])

        kb = None
        if buttons:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn["text"], url=btn["url"])] for btn in buttons
            ])

        media_files: list[MediaUnion] = []
        if media:
            for url in media:
                if media_type == "photo":
                    media_files.append(InputMediaPhoto(media=url))
                elif media_type == "video":
                    media_files.append(InputMediaVideo(media=url))
                # FIXME: Cant send GIF and Document
                #elif media_type == "document":
                #    media_files.append(InputMediaDocument(media=url))
                #elif media_type == "gif":
                #    media_files.append(InputMediaAnimation(media=url))
                else:
                    print(f"[INFO] Неизвестный тип медиа: {media_type}")

        try:
            if media_files:
                if event.bot:
                    await event.bot.send_media_group(chat_id=event.chat.id, media=media_files)

            if text and isinstance(text, str):
                await event.answer(text, reply_markup=kb)
            elif kb:
                await event.answer(" ", reply_markup=kb)
        except Exception as e:
            print(f"[media error]: {e}")
            
    async def get_channels(self, ads: list[Ad]) -> tuple[dict[str, str], dict[str, str]]:
        ns_channels: dict[str, str] = {}
        os_channels: dict[str, str] = {}

        for ad in ads:
            if ad.get("type") == "NS":
                channels = ad.get("channels", {})
                ns_channels.update(channels)
            elif ad.get("type") == "OS":
                channels = ad.get("channels", {})
                os_channels.update(channels)

        return ns_channels, os_channels