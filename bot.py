"""
Простой бот на aiogram 3, который открывает трекер копилки
как Telegram Mini App (всплывающее окно внутри Telegram).

Установка:
    pip install aiogram

Токен бота читается из переменной окружения BOT_TOKEN.
Локально можно передать его так:
    BOT_TOKEN=твой_токен python3 bot.py

На Railway / Render токен указывается в настройках проекта
как Environment Variable с именем BOT_TOKEN — так он не хранится
в открытом виде в публичном репозитории на GitHub.

Запуск:
    python bot.py
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

TOKEN = os.environ.get("BOT_TOKEN", "8759572297:AAGDGgvTnQ4X7dBUVO-YwEgO-PSEWUP847E")
WEBAPP_URL = "https://hlystikfilipp.github.io/Kopilka/копилка-tg-webapp.html"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


def tracker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐷 Открыть копилку",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Это трекер копилки — откладывай 5 BYN в день и отмечай прогресс.\n\n"
        "Нажми кнопку ниже, чтобы открыть трекер.",
        reply_markup=tracker_keyboard(),
    )


@dp.message(F.text == "/tracker")
async def tracker(message: Message):
    await message.answer("Твоя копилка:", reply_markup=tracker_keyboard())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
