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

from .types import Ad, AdH, AdOS, AdNS, FullUserData, ServePayload, Button


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
            chosen_ad_type = ad.get("chosen_ad_type")

            if ad_type == "H":
                # Сохраняем все типы и ссылки на медиа
                media_urls: list[str] = []
                media_types: list[str] = []

                for media in ad.get("media", []):
                    url = media.get("url")
                    m_type = media.get("type")
                    if url and m_type:
                        media_urls.append(url)
                        media_types.append(m_type)

                # Кнопки — берём redirect если chosen_ad_type == "clicks"
                buttons: list[Button] = []
                for btn in ad.get("tg_buttons", []):
                    url_field = (
                        btn.get("redirect")
                        if chosen_ad_type == "clicks"
                        else btn.get("url")
                    )
                    if btn.get("text") and url_field:
                        buttons.append({"text": btn["text"], "url": url_field})

                ads.append(
                    AdH(
                        type="H",
                        text=ad.get("tg_text", ""),
                        media_type=media_types[0],
                        media=media_urls,
                        buttons=buttons,
                    )
                )

            elif ad_type == "NS":
                channels = ad.get("channels")
                if not channels and ad.get("tg_buttons"):
                    channels = {
                        btn["text"]: btn["redirect"]
                        if ad.get("chosen_ad_type") == "clicks"
                        else btn["url"]
                        for btn in ad["tg_buttons"]
                        if btn.get("text") and (btn.get("redirect") or btn.get("url"))
                    }
                ads.append(AdNS(type="NS", channels=channels or {}))

            elif ad_type == "OS":
                channels = ad.get("channels")
                if not channels and ad.get("tg_buttons"):
                    channels = {
                        btn["text"]: btn["redirect"]
                        if ad.get("chosen_ad_type") == "clicks"
                        else btn["url"]
                        for btn in ad["tg_buttons"]
                        if btn.get("text") and (btn.get("redirect") or btn.get("url"))
                    }
                ads.append(AdOS(type="OS", channels=channels or {}))
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

        media_type = ad.get("media_type", "photo").lower()
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

        try:
            if event.bot and media:
                if media_type in ("photo", "video"):
                    media_files: list[MediaUnion] = []
                    for url in media:
                        if media_type == "photo":
                            media_files.append(InputMediaPhoto(media=url))
                        elif media_type == "video":
                            media_files.append(InputMediaVideo(media=url))

                    if media_files:
                        await event.bot.send_media_group(
                            chat_id=event.chat.id, media=media_files
                        )

                elif media_type == "document":
                    await event.bot.send_document(
                        chat_id=event.chat.id, document=media[0]
                    )

                elif media_type in ("gif", "animation"):
                    await event.bot.send_animation(
                        chat_id=event.chat.id, animation=media[0]
                    )

                else:
                    print(f"[INFO] Неизвестный тип медиа: {media_type}")

            # Отправка текста и кнопок
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
