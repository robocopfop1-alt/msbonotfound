import asyncio
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

TOKEN = "8902901317:AAGJmW49Czu6PG1FqNj_Xj8MAFEE9GfdK5A"
ADMIN_ID = 8404046302

DATA_FILE = "users.json"

PHOTO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hello.PNG")

bot = Bot(TOKEN)
dp = Dispatcher()

users = {}
admin_states = {}

ITEM_MESSAGES = {
    "item1": "Скиньте 80 звёзд на данный аккаунт - @ufyty\n\n(p.s. когда скидываете подарок, напишите в сообщении какой номер вам нужен - Физический номер +1 (США))",
    "item2": "Скиньте 25 звёзд на данный аккаунт - @ufyty\n\n(p.s. когда скидываете подарок, напишите в сообщении какой номер вам нужен - Виртуальный номер +91 (Индия))",
    "item3": "Скиньте 40 звёзд на данный аккаунт - @ufyty\n\n(p.s. когда скидываете подарок, напишите в сообщении какой номер вам нужен - Физический номер +1 (Канада))",
    "item4": "Скиньте 150 звёзд на данный аккаунт - @ufyty\n\n(p.s. когда скидываете подарок, напишите в сообщении какой номер вам нужен - Физический номер +7 (Россия))",
    "item5": "Скиньте 100 звёзд на данный аккаунт - @ufyty\n\n(p.s. когда скидываете подарок, напишите в сообщении какой номер вам нужен - Физический номер +380 (Украина))",
}

SHOP_TEXT = (
    "В продаже:\n\n"
    "/1 - Физический номер +1 (США) - 80 зв / 100 руб\n"
    "/2 - Виртуальный номер +91 (Индия) - 25 зв / 40 руб\n"
    "/3 - Физический номер +1 (Канада) - 40 зв / 50-60 руб\n"
    "/4 - Физический номер +7 (Россия) - 150 зв / 200-250 руб\n"
    "/5 - Физический номер +380 (Украина) - 100 зв / 150 руб"
)


def load_data():
    global users
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    else:
        users = {}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти в магазин", callback_data="shop")],
            [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        ]
    )


def admin_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить сообщение", callback_data="broadcast")]
        ]
    )


def shop_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="/1 - Физический номер +1 (США)", callback_data="item1")],
            [InlineKeyboardButton(text="/2 - Виртуальный номер +91 (Индия)", callback_data="item2")],
            [InlineKeyboardButton(text="/3 - Физический номер +1 (Канада)", callback_data="item3")],
            [InlineKeyboardButton(text="/4 - Физический номер +7 (Россия)", callback_data="item4")],
            [InlineKeyboardButton(text="/5 - Физический номер +380 (Украина)", callback_data="item5")],
            [InlineKeyboardButton(text="Назад", callback_data="main")],
        ]
    )


def back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="main")]
        ]
    )


def get_time_in_bot(user_id):
    started = datetime.fromtimestamp(float(users[str(user_id)]["started_at"]))
    delta = datetime.now() - started
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{days} дн {hours} ч {minutes} мин"


def _message_has_photo(message):
    return isinstance(message, Message) and bool(message.photo)


async def _show_text(message, text, kb):
    if _message_has_photo(message):
        await message.delete()
        await message.answer(text, reply_markup=kb)
    else:
        await message.edit_text(text, reply_markup=kb)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Нет"
    username = message.from_user.username or "Нет"

    if str(user_id) not in users:
        users[str(user_id)] = {
            "first_name": first_name,
            "username": username,
            "started_at": str(datetime.now().timestamp()),
        }
        save_data()

    if user_id == ADMIN_ID:
        photo = FSInputFile(PHOTO_PATH)
        await message.answer_photo(photo, reply_markup=admin_menu_kb())
    else:
        photo = FSInputFile(PHOTO_PATH)
        await message.answer_photo(photo, reply_markup=main_menu_kb())


@dp.callback_query(F.data == "main")
async def cb_main(callback: CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await _show_text(
            callback.message,
            "Приветствую, админ! Выберите нужные вам разделы ниже.",
            admin_menu_kb(),
        )
    else:
        await _show_text(
            callback.message,
            "Приветствую в Attack Shop Bot. Выберите нужные вам разделы ниже.",
            main_menu_kb(),
        )
    await callback.answer()


@dp.callback_query(F.data == "shop")
async def cb_shop(callback: CallbackQuery):
    await _show_text(callback.message, SHOP_TEXT, shop_kb())
    await callback.answer()


@dp.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    first_name = callback.from_user.first_name or "Нет"
    username = callback.from_user.username or "Нет"
    text = (
        f"Профиль:\n\n"
        f"Ник: {first_name}\n"
        f"Юзернейм: @{username}\n"
        f"ID: {user_id}\n"
        f"В боте: {get_time_in_bot(user_id)}"
    )
    await _show_text(callback.message, text, back_kb())
    await callback.answer()


@dp.callback_query(F.data.startswith("item"))
async def cb_item(callback: CallbackQuery):
    text = ITEM_MESSAGES.get(callback.data, "Что-то пошло не так.")
    await _show_text(callback.message, text, back_kb())
    await callback.answer()


@dp.callback_query(F.data == "broadcast")
async def cb_broadcast(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    admin_states[callback.from_user.id] = "awaiting_broadcast"
    await _show_text(callback.message, "Введите сообщение.", back_kb())
    await callback.answer()


@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID and admin_states.get(user_id) == "awaiting_broadcast":
        admin_states[user_id] = None
        text = message.text
        sent = 0
        for uid in users.keys():
            try:
                await bot.send_message(int(uid), text)
                sent += 1
            except Exception:
                continue
        await message.answer(f"Сообщение отправлено {sent} пользователям.")
        return


async def main():
    load_data()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())