from config import BOT_TOKEN
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sdk import SubscriptionMiddleware

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Sdk integration example
global_mw = SubscriptionMiddleware(
    sdk_key="test",
    max_channels=3,
    dispatcher=dp
)
dp.message.middleware(global_mw)
dp.callback_query.middleware(global_mw)

global_mw.register_check_subscription_handler(dp)

router_main = Router()
router_admin = Router()

# Обработчик команды /start
@router_main.message(CommandStart())
async def cmd_start(msg: types.Message):
    # Клавиатура с кнопкой "Тест"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="test_button")]
    ])
    await msg.answer("Добро пожаловать! Нажмите на кнопку для теста:", reply_markup=keyboard)

# Обработчик для кнопки "Тест"
@dp.callback_query(F.data == "test_button")
async def test_button_handler(call: types.CallbackQuery):
    print(f"[INFO] Обработан callback: {call.data}")
    await call.answer("Тестовое сообщение!")


# Обработчик для текста "admin"
@router_admin.message(F.text == "admin")
async def admin_panel(msg: types.Message):
    await msg.answer("Админ-панель.")

dp.include_router(router_main)
dp.include_router(router_admin)

# Запуск бота
async def main():
    await dp.start_polling(bot) # type: ignore

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
