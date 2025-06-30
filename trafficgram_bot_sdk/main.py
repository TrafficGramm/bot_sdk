from typing import Dict, Any, Callable, Awaitable, Optional
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, Update
from .ads import AdService
from .logging_utils import LoggingService
from .utils import get_channels_keyboard
from .types import Ad, FullUserData

import datetime
import time

CHECK_BUTTON_TEXT = "🔄 Проверить подписку"


class SubscriptionMiddleware:
    BASE_API_URL = "https://core-backsdk.infra.trafficgram.online"
    CHECKER_API_URL = "http://127.0.0.1:8080"

    CHANNELS_API_URL = f"{BASE_API_URL}/bot_serve"
    CHECK_API_URL = f"{CHECKER_API_URL}/check-subscription"
    LOG_API_URL = f"{BASE_API_URL}/bot_events"
    AD_GOAL_API_URL = f"{BASE_API_URL}/bot_ad_goal"

    def __init__(
        self,
        sdk_key: str,
        dispatcher: Dispatcher,
        not_subscribed_message: Optional[str] = None,
        max_channels: int = 5,
    ):
        self.sdk_key = sdk_key
        self.ad_service = AdService(
            channels_api_url=self.CHANNELS_API_URL,
            check_api_url=self.CHECK_API_URL,
            sdk_key=self.sdk_key,
        )
        self.log_service = LoggingService(log_api_url=self.LOG_API_URL, sdk_key=sdk_key)
        self.dispatcher = dispatcher
        self.not_subscribed_message = (
            not_subscribed_message or "Подпишитесь на каналы для доступа:"
        )
        self.max_channels = max_channels
        self.user_ad_shown: Dict[int, bool] = {}
        self.pending_channels: Dict[int, Dict[str, str]] = {}
        self.log_all = True

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
            user_id = user.id if user else 0
            event_type = "message"
            content = event.text
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            user_id = user.id
            event_type = "callback_query"
            content = event.data
        else:
            return await handler(event, data)

        if user is not None:
            full_user_data = FullUserData(
                id=user.id,
                is_bot=user.is_bot,
                is_premium=getattr(user, "is_premium", False),
                language_code=user.language_code or "",
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
            )
        else:
            full_user_data: FullUserData = {}

        if self.log_all:
            await self.log_service.send_action_log(
                user_id,
                full_user_data=full_user_data,
                event_type=event_type,
                details={
                    "text": str(content),
                    "event_id": str(
                        getattr(event, "message_id", None) or getattr(event, "id", None)
                    ),
                },
            )

        if (
            isinstance(event, Message)
            and isinstance(event.text, str)
            and event.text.startswith("/start")
        ):
            if self.user_ad_shown.get(user_id):
                self.user_ad_shown[user_id] = False
                return await handler(event, data)

            start_param = event.text.split("?", 1)[1] if "?" in event.text else None

            if user_id in self.pending_channels:
                all_channels = self.pending_channels[user_id]
                if all_channels:
                    kb = get_channels_keyboard(all_channels, self.max_channels)
                    text = (
                        self.not_subscribed_message
                        + "\n\n"
                        + "\n".join(
                            f"• <a href='{url}'>{name}</a>"
                            for name, url in all_channels.items()
                        )
                    )
                    await event.answer(text, reply_markup=kb, parse_mode="HTML")
                    return

            ads: list[Ad] = await self.ad_service.fetch_ad(
                user_id, full_user_data=full_user_data
            )

            for ad in ads:
                if ad.get("type") == "H":
                    await self.ad_service.handle_h_ad(event, ad)
                    self.user_ad_shown[user_id] = True

                    fake_message = Message(
                        message_id=event.message_id,
                        date=datetime.datetime.now(datetime.timezone.utc),
                        chat=event.chat,
                        from_user=event.from_user,
                        text=f"/start?{start_param}" if start_param else "/start",
                    )
                    update = Update(update_id=int(time.time()), message=fake_message)

                    data["fake_start"] = True
                    data["skip_subscriptions"] = True
                    if event.bot:
                        await self.dispatcher.feed_update(event.bot, update)
                    return

            if not data.get("skip_subscriptions"):
                ns_channels, os_channels = await self.ad_service.get_channels(ads)
                all_channels = {**ns_channels, **os_channels}

                if ns_channels:
                    self.pending_channels[user_id] = ns_channels

                if all_channels:
                    kb = get_channels_keyboard(all_channels, self.max_channels)
                    text = (
                        self.not_subscribed_message
                        + "\n\n"
                        + "\n".join(
                            f"• <a href='{url}'>{name}</a>"
                            for name, url in all_channels.items()
                        )
                    )
                    await event.answer(text, reply_markup=kb, parse_mode="HTML")
                    return

        return await handler(event, data)

    def register_check_subscription_handler(self, dp: Dispatcher):
        from .actions import check_subscription_handler

        check_subscription_handler(dp, self.ad_service, self)
