from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, Update, InlineKeyboardMarkup, InlineKeyboardButton

import aiohttp
import time
import datetime
from sdk.ads import AdService
from sdk.main import SubscriptionMiddleware

def check_subscription_handler(dp: Dispatcher, ad_service: AdService, middleware: SubscriptionMiddleware):
    @dp.callback_query(F.data == "check_subscription")
    async def check_subscription_handler(call: CallbackQuery): # type: ignore[reportUnusedFunction]
        print("[INFO] Обработчик для check_subscription активирован.")
        await call.answer("Проверяем подписку...")
        user_id = call.from_user.id

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:8000/channels", params={"user_id": user_id}) as resp:
                    ads = await resp.json()
                    if not ads:
                        raise ValueError("Не удалось получить данные о каналах.")
        except Exception as e:
            await call.answer(f"Ошибка при получении данных: {e}", show_alert=True)
            return
            
        ns_channels, os_channels = await ad_service.get_channels(ads)

        all_channels: dict[str, str] = {**ns_channels, **os_channels}

        not_subscribed: list[tuple[str, str]] = []
        for name, url in list(ns_channels.items())[:5]:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://127.0.0.1:8000/is_subscribed", json={"user_id": user_id, "channel_url": url}) as resp:
                    result = await resp.json()
                    if not result.get("subscribed", False):
                        not_subscribed.append((name, url))
        if call.message:
            if not_subscribed:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=name, url=url)] for name, url in all_channels.items()
                ] + [[InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_subscription")]])
                text = "Подпишитесь на каналы для доступа:\n\n" + "\n".join(
                    f"• <a href='{url}'>{name}</a>" for name, url in all_channels.items()
                )
                await call.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
                await call.answer("Вы ещё не подписались на все каналы!", show_alert=True)
            else:
                await call.message.answer("✅ Спасибо! Подписка проверена. Доступ открыт.")
                await call.answer("Подписка подтверждена!")

            middleware.user_ad_shown[user_id] = True
            start_param = str(call.data).split('?')[1] if '?' in str(call.data) else None

            fake_message = Message(
                message_id=call.message.message_id,
                date=datetime.datetime.now(datetime.timezone.utc),
                chat=call.message.chat,
                from_user=call.from_user,
                text=f"/start?{start_param}" if start_param else "/start"
            )

            update = Update(update_id=int(time.time()), message=fake_message)
            if call.bot:
                await dp.feed_update(call.bot, update)
