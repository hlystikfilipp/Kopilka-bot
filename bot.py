"""
Бот на aiogram 3, который открывает трекер копилки как Telegram
Mini App (всплывающее окно внутри Telegram) и умеет присылать
ежедневное напоминание в выбранное пользователем время.

Установка:
    pip install aiogram tzdata

Токен бота читается из переменной окружения BOT_TOKEN.
Локально можно передать его так:
    BOT_TOKEN=твой_токен python3 bot.py

На Railway / Render токен указывается в настройках проекта
как Environment Variable с именем BOT_TOKEN — так он не хранится
в открытом виде в публичном репозитории на GitHub.

Команды бота:
    /start            — приветствие и кнопка с трекером
    /tracker          — открыть трекер
    /remind ЧЧ:ММ     — включить/изменить ежедневное напоминание
    /remind off       — выключить напоминание
    /remind           — посмотреть текущую настройку

Запуск:
    python bot.py
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

TOKEN = os.environ.get("BOT_TOKEN", "8759572297:AAGDGgvTnQ4X7dBUVO-YwEgO-PSEWUP847E")
WEBAPP_URL = "https://hlystikfilipp.github.io/Kopilka/копилка-tg-webapp.html"

# Часовой пояс, в котором интерпретируется введённое пользователем время.
# Минск — UTC+3.
TIMEZONE = ZoneInfo("Europe/Minsk")

# Файл, где хранятся выбранные пользователями времена напоминаний.
# Важно: на некоторых хостингах (например, Railway без подключённого
# постоянного диска) файловая система сбрасывается при каждом новом
# деплое — тогда настройки времени тоже сбросятся, и их нужно будет
# задать заново командой /remind.
REMINDERS_FILE = "reminders.json"

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


def load_reminders() -> dict:
    if not os.path.exists(REMINDERS_FILE):
        return {}
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_reminders(data: dict) -> None:
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


reminders = load_reminders()  # {"<chat_id>": "HH:MM"}
already_sent_today: dict[str, str] = {}  # {"<chat_id>": "YYYY-MM-DD"}


def tracker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Открыть копилку",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Это трекер копилки — откладывай деньги каждый день "
        "и отмечай прогресс.\n\n"
        "Нажми кнопку ниже, чтобы открыть трекер.\n\n"
        "Хочешь, буду присылать ежедневное напоминание? "
        "Напиши, например: /remind 20:00",
        reply_markup=tracker_keyboard(),
    )


@dp.message(F.text == "/tracker")
async def tracker(message: Message):
    await message.answer("Твоя копилка:", reply_markup=tracker_keyboard())


@dp.message(Command("remind"))
async def remind(message: Message):
    chat_id = str(message.chat.id)
    args = message.text.replace("/remind", "", 1).strip()

    if not args:
        current = reminders.get(chat_id)
        if current:
            await message.answer(
                f"Сейчас напоминание приходит каждый день в {current} (время Минска).\n\n"
                "Чтобы изменить: /remind ЧЧ:ММ\n"
                "Чтобы выключить: /remind off"
            )
        else:
            await message.answer(
                "Напоминание пока не настроено.\n\n"
                "Включить: /remind ЧЧ:ММ, например /remind 20:00"
            )
        return

    if args.lower() == "off":
        if chat_id in reminders:
            del reminders[chat_id]
            save_reminders(reminders)
        await message.answer("Напоминание выключено.")
        return

    match = TIME_RE.match(args)
    if not match:
        await message.answer(
            "Не понял время. Пришли в формате ЧЧ:ММ, например: /remind 20:00"
        )
        return

    reminders[chat_id] = args
    save_reminders(reminders)
    await message.answer(f"Готово! Буду напоминать каждый день в {args} (время Минска).")


async def reminder_loop():
    """Раз в минуту проверяет, не пора ли кому-то отправить напоминание."""
    while True:
        now = datetime.now(TIMEZONE)
        current_hm = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        for chat_id, target_hm in list(reminders.items()):
            if target_hm != current_hm:
                continue
            if already_sent_today.get(chat_id) == today:
                continue
            try:
                await bot.send_message(
                    chat_id,
                    "💰 Не забудь отложить сегодняшнюю сумму в копилку!",
                    reply_markup=tracker_keyboard(),
                )
            except Exception as e:
                logging.warning("Не удалось отправить напоминание %s: %s", chat_id, e)
            already_sent_today[chat_id] = today

        await asyncio.sleep(30)


async def main():
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
