from aiogram import Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import aiohttp
import time
import datetime
from .ads import AdService
from .main import SubscriptionMiddleware
from .types import FullUserData, Ad


def check_subscription_handler(
    dp: Dispatcher, ad_service: AdService, middleware: SubscriptionMiddleware
):
    @dp.callback_query(F.data == "check_subscription")
    async def check_subscription_handler(call: CallbackQuery):  # type: ignore[reportUnusedFunction]
        await call.answer("Проверяем подписку...")
        user = call.from_user
        user_id = user.id

        all_channels = middleware.pending_channels.get(user_id)
        if not all_channels:
            ads: list[Ad] = await ad_service.fetch_ad(user_id)
            ns_channels, os_channels = await ad_service.get_channels(ads)
            all_channels = {**ns_channels, **os_channels}
            middleware.pending_channels[user_id] = all_channels

        not_subscribed: list[tuple[str, str]] = []
        for name, url in list(all_channels.items())[:5]:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    middleware.CHECK_API_URL, json={"user_id": user_id, "channel": url}
                ) as resp:
                    result = await resp.json()
                    if not result.get("subscribed", False):
                        not_subscribed.append((name, url))

        if call.message:
            if not_subscribed:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=name, url=url)]
                        for name, url in all_channels.items()
                    ]
                    + [
                        [
                            InlineKeyboardButton(
                                text="🔄 Проверить подписку",
                                callback_data="check_subscription",
                            )
                        ]
                    ]
                )
                text = "Подпишитесь на каналы для доступа:\n\n" + "\n".join(
                    f"• <a href='{url}'>{name}</a>"
                    for name, url in all_channels.items()
                )
                await call.message.answer(
                    text, reply_markup=keyboard, parse_mode="HTML"
                )
                await call.answer(
                    "Вы ещё не подписались на все каналы!", show_alert=True
                )
            else:
                await call.message.answer(
                    "✅ Спасибо! Подписка проверена. Доступ открыт."
                )
                await call.answer("Подписка подтверждена!")

                # Удаляем кэш
                middleware.pending_channels.pop(user_id, None)

                # Отправка ad_goal
                full_user_data: FullUserData = {
                    "id": user.id,
                    "is_bot": user.is_bot,
                    "is_premium": getattr(user, "is_premium", False),
                    "language_code": user.language_code or "",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                }

                ad_goal_payload: dict[str, str | FullUserData] = {
                    "telegram_user_id": str(user_id),
                    "full_user_data": full_user_data,
                }

                headers = {
                    "X-Sdk-Key": middleware.sdk_key,
                    "Content-Type": "application/json",
                }

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            middleware.AD_GOAL_API_URL,
                            json=ad_goal_payload,
                            headers=headers,
                        ) as resp:
                            if resp.status != 200:
                                print(
                                    f"[ERROR] ad_goal failed: {resp.status} {await resp.text()}"
                                )
                except Exception as e:
                    print(f"[ERROR] ad_goal exception: {e}")

                # Генерация поддельного /start
                middleware.user_ad_shown[user_id] = True
                start_param = (
                    str(call.data).split("?")[1] if "?" in str(call.data) else None
                )

                fake_message = Message(
                    message_id=call.message.message_id,
                    date=datetime.datetime.now(datetime.timezone.utc),
                    chat=call.message.chat,
                    from_user=call.from_user,
                    text=f"/start?{start_param}" if start_param else "/start",
                )

                update = Update(update_id=int(time.time()), message=fake_message)
                if call.bot:
                    await dp.feed_update(call.bot, update)
