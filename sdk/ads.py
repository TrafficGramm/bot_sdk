import aiohttp
from typing import Any
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    MediaUnion,
    Message,
)

from sdk.types import Ad, AdH, AdOS, AdNS, FullUserData, ServePayload


class AdService:
    def __init__(self, channels_api_url: str, check_api_url: str, sdk_key: str):
        self.sdk_key = sdk_key
        self.serve_api_url = channels_api_url
        self.check_api_url = check_api_url

    @staticmethod
    def normalize_ads(raw_ads: list[dict[str, Any]]) -> list[Ad]:
        ads: list[Ad] = []
        for ad in raw_ads:
            ad_type = ad.get("format")
            if ad_type == "H":
                ads.append(
                    AdH(
                        type="H",
                        text=ad.get("tg_text", ""),
                        media_type=ad["media"][0]["type"] if ad.get("media") else "",
                        media=ad["media"][0]["url"] if ad.get("media") else "",
                        buttons=[
                            {"text": b["text"], "url": b["url"]}
                            for b in ad.get("tg_buttons", [])
                        ],
                    )
                )
            elif ad_type == "NS":
                ads.append(AdNS(type="NS", channels=ad.get("channels", {})))
            elif ad_type == "OS":
                ads.append(AdOS(type="OS", channels=ad.get("channels", {})))
        return ads

    async def fetch_ad(
        self, user_id: int, full_user_data: FullUserData | None = None
    ) -> list[Ad]:
        if full_user_data is None:
            full_user_data = {}

        headers = {"X-Sdk-Key": self.sdk_key, "Content-Type": "application/json"}

        payload: ServePayload = {
            "telegram_user_id": str(user_id),
            "is_premium": int(full_user_data.get("is_premium") or False),
            "full_user_data": full_user_data,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.serve_api_url, json=payload, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    raw_ads = await resp.json()
                    return AdService.normalize_ads(raw_ads)
            except Exception as e:
                print(f"[ERROR] Ошибка при получении рекламы: {e}")
                return []

    async def is_user_subscribed(self, user_id: int, channel_url: str) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                print(self.check_api_url)
                async with session.post(
                    self.check_api_url,
                    json={"user_id": user_id, "channel_url": channel_url},
                ) as resp:
                    result = await resp.json()
                    return result.get("subscribed", False)
            except Exception as e:
                print(f"[ERROR] Ошибка при проверке подписки: {e}")
                return False

    async def handle_h_ad(self, event: Message, ad: Ad):
        media_raw: str | list[str] = ad.get("media", [])
        media: list[str] = (
            [media_raw] if isinstance(media_raw, str) else media_raw or []
        )

        media_type = ad.get("media_type", "photo")
        text = ad.get("text", "")
        buttons = ad.get("buttons", [])

        kb = None
        if buttons:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=btn["text"], url=btn["url"])]
                    for btn in buttons
                ]
            )

        # FIXME: Fix problem with sending media and text in difference msg
        media_files: list[MediaUnion] = []
        if media:
            for url in media:
                if media_type == "photo":
                    media_files.append(InputMediaPhoto(media=url))
                elif media_type == "video":
                    media_files.append(InputMediaVideo(media=url))
                # FIXME: Cant send GIF and Document
                # elif media_type == "document":
                #    media_files.append(InputMediaDocument(media=url))
                # elif media_type == "gif":
                #    media_files.append(InputMediaAnimation(media=url))
                else:
                    print(f"[INFO] Неизвестный тип медиа: {media_type}")

        try:
            if media_files:
                if event.bot:
                    await event.bot.send_media_group(
                        chat_id=event.chat.id, media=media_files
                    )

            if text and isinstance(text, str):
                await event.answer(text, reply_markup=kb)
            elif kb:
                await event.answer(" ", reply_markup=kb)
        except Exception as e:
            print(f"[media error]: {e}")

    async def get_channels(
        self, ads: list[Ad]
    ) -> tuple[dict[str, str], dict[str, str]]:
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
