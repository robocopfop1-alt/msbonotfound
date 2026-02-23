import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8725062823:AAH3jJDkKWlJQVi8_loRIUUk3R1CLbXtM-g"  # Ваш токен
ADMIN_ID = 7021546295  # Ваш Telegram ID
PAYMENT_LINK = "t.me/send?start=IVHDcTIbUZpX"  # Ссылка на оплату
SUPPORT_USERNAME = "incelbec"  # Юзернейм саппорта (без @)
# ===============================

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Словарь для хранения подписок: {user_id: дата_окончания}
# В реальном проекте лучше использовать базу данных (SQLite/PostgreSQL)
subscriptions = {}

# Машина состояний для админ-панели
class AdminStates(StatesGroup):
    waiting_for_username = State()  # Ждем юзернейм для выдачи подписки

# ========== ФУНКЦИИ-ЗАГЛУШКИ (ОПАСНЫЙ ФУНКЦИОНАЛ) ==========
async def fake_report_user(target_username: str, admin_id: int):
    """
    ИМИТАЦИЯ РАБОТЫ.
    В реальности тут должен быть код для отправки жалоб через Telegram,
    но это нарушает правила. Поэтому просто пишем в логи.
    """
    await bot.send_message(
        admin_id,
        f"⚠️ Демо-режим: Попытка начать жалобы на пользователя @{target_username}.\n"
        f"❌ Реальный 'снос' не выполнен, так как это нарушает правила Telegram.\n"
        f"ℹ️ Если бы это был реальный код, здесь была бы логика отправки 100+ жалоб."
    )
    # Здесь могла бы быть ваша логика, но бот будет забанен.
    return True
# ===========================================================

# ========== ОБРАБОТЧИКИ КОМАНД ==========

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Главное меню с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍕 Заказать пиццу", callback_data="order_pizza")],
        [InlineKeyboardButton(text="⭐ Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])
    
    await message.answer(
        "Приветствую в GREATPIZA 🍕\n\n"
        "Чтобы заказать пиццу используйте кнопки ниже.",
        reply_markup=keyboard
    )

# ========== ОБРАБОТЧИКИ КНОПОК ==========

@dp.callback_query(F.data == "order_pizza")
async def process_order_pizza(callback: CallbackQuery):
    await callback.answer()  # Убираем "часики" на кнопке
    await callback.message.answer(
        "🍕 Раздел заказа пиццы временно находится в разработке.\n"
        "Пожалуйста, оформите подписку для доступа к заказу."
    )

@dp.callback_query(F.data == "subscribe")
async def process_subscribe(callback: CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить подписку", url=PAYMENT_LINK)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")]
    ])
    await callback.message.answer(
        "⭐ Оформление подписки\n\n"
        "1. Нажмите кнопку ниже для оплаты.\n"
        "2. После оплаты нажмите 'Я оплатил'.",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "paid")
async def process_paid(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        f"✅ Спасибо за оплату!\n"
        f"Обратитесь в поддержку: @{SUPPORT_USERNAME} для активации подписки."
    )

@dp.callback_query(F.data == "support")
async def process_support(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        f"🆘 Служба поддержки: @{SUPPORT_USERNAME}\n"
        "Напишите ему напрямую для решения вопросов."
    )

# ========== АДМИН-ПАНЕЛЬ (ДЛЯ ВАС) ==========

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Выдать подписку по юзернейму", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="📋 Список активных подписок", callback_data="admin_list_subs")]
    ])
    await message.answer("🔐 Админ-панель", reply_markup=keyboard)

# Выдача подписки
@dp.callback_query(F.data == "admin_give_sub")
async def admin_give_sub_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("Введите юзернейм пользователя (например, username):")
    await state.set_state(AdminStates.waiting_for_username)

@dp.message(AdminStates.waiting_for_username)
async def admin_process_username(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    
    username = message.text.strip().replace('@', '')  # Убираем @ если ввели
    # Ищем пользователя по юзернейму (сложно в Telegram API без username)
    # Упростим: будем считать, что подписка выдается на username как на строку
    # В реальности нужно либо заставить пользователя написать боту, либо использовать user_id
    
    # Пытаемся найти user_id по username (только если пользователь взаимодействовал с ботом)
    # Это упрощенный вариант: сохраняем подписку как "username: дата"
    # Для полноценной работы нужна БД и связка username -> user_id
    
    # Выдаем подписку на 30 дней
    expiry_date = datetime.now() + timedelta(days=30)
    
    # Сохраняем в наш "фейковый" словарь
    # В реальности нужно хранить по user_id, но для демо - по username
    subscriptions[username] = expiry_date
    
    await message.answer(f"✅ Подписка выдана пользователю @{username} до {expiry_date.strftime('%d.%m.%Y')}")
    
    # Теперь запускаем "фейковый снос" (просто уведомление)
    await fake_report_user(username, ADMIN_ID)
    
    await state.clear()

@dp.callback_query(F.data == "admin_list_subs")
async def admin_list_subs(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    await callback.answer()
    
    if not subscriptions:
        await callback.message.answer("📭 Нет активных подписок.")
        return
    
    text = "📋 Активные подписки:\n\n"
    for username, expiry in subscriptions.items():
        status = "✅" if expiry > datetime.now() else "❌"
        text += f"{status} @{username} - до {expiry.strftime('%d.%m.%Y')}\n"
    
    await callback.message.answer(text)

# Проверка подписки (пример)
@dp.message()
async def check_subscription(message: Message):
    # Если сообщение не команда и не callback, просто игнорируем
    pass

# ========== ЗАПУСК БОТА ==========
async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
