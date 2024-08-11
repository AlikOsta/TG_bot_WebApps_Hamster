import sqlite3
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CHANNEL_ID = os.getenv("CHANNEL_ID")
PHOTO_URL = os.getenv("PHOTO_URL")
KEYS_WEB_APP_URL = os.getenv("KEYS_WEB_APP_URL")
SUBSCRIBE_URL = os.getenv("SUBSCRIBE_URL")
API_TOKEN = os.getenv("API_TOKEN")
id_admin = int(os.getenv("id_admin"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


def user_exists(user_id: int) -> bool:
    with sqlite3.connect("users.db") as bd:
        cursor = bd.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE
            )
        ''')
        cursor.execute('''
            SELECT 1 FROM users WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchone() is not None


def add_user(user_id: int):
    with sqlite3.connect("users.db") as bd:
        cursor = bd.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id) VALUES (?)
        ''', (user_id,))
        bd.commit()


def get_subscribe_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подписаться", url=SUBSCRIBE_URL)],
        [InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")]
    ])


def get_keys_markup():

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить ключи!!!", web_app=WebAppInfo(url=KEYS_WEB_APP_URL))]
    ])


async def send_photo_with_markup(message: types.Message, caption: str, markup: InlineKeyboardMarkup):
    try:
        await message.answer_photo(
            photo=PHOTO_URL,
            caption=caption,
            reply_markup=markup
        )
    except Exception as e:
        await message.answer("Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.")
        print(f"Error: {e}")


@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    print(f'Старт + {message.chat.id}')
    user_id = message.from_user.id

    if not message.from_user.is_bot:
        if not user_exists(user_id):
            add_user(user_id)
            print(f'Регистрация + {user_id}')

        try:
            member = await bot.get_chat_member(CHANNEL_ID, user_id)

            if member.status in ['member', 'administrator', 'creator']:
                await send_photo_with_markup(
                    message,
                    "Привет, халявные ключи для тебя и твоих корешей!!!",
                    get_keys_markup()
                )
            else:
                await send_photo_with_markup(
                    message,
                    "Пожалуйста, подпишитесь на @smartkeyham, чтобы получить ключи.",
                    get_subscribe_markup()
                )
        except Exception as e:
            await message.answer("Произошла ошибка при проверке подписки. Пожалуйста, попробуйте позже.")
            print(f"Error: {e}")


@dp.callback_query(lambda c: c.data == 'check_subscription')
async def check_subscription(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)

        if member.status in ['member', 'administrator', 'creator']:
            await bot.edit_message_media(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                media=InputMediaPhoto(media=PHOTO_URL, caption="Привет, халявные ключи для тебя и твоих корешей!!!"),
                reply_markup=get_keys_markup()
            )
        else:
            await bot.edit_message_caption(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                caption="Ты не подписался на @smartkeyham!!! Сделай уже это и возвращайся обратно.",
                reply_markup=get_subscribe_markup()
            )
    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при проверке подписки. Пожалуйста, попробуйте позже.")
        print(f"Error: {e}")


@dp.message(Command(commands=['users']))
async def users(message: types.Message):
    if message.from_user.id == id_admin:
        await print_users(message)
    else:
        await message.answer("Эта команда доступна только администратору!")


async def print_users(message: types.Message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id ASC")

    info_user = ""
    for user in cursor.fetchall():
        info_user += f"{user[0]}: {user[1]}\n"

    cursor.close()
    conn.close()
    await message.answer(info_user)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
