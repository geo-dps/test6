```python
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message


# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена")


# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Команда /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я простой Telegram-бот.\n"
        "Напиши мне что-нибудь, и я отвечу."
    )


# Команда /help
@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📋 Доступные команды:\n\n"
        "/start — запустить бота\n"
        "/help — показать помощь"
    )


# Ответ на обычные сообщения
@dp.message()
async def message_handler(message: Message):
    await message.answer(
        f"Ты написал:\n\n{message.text}"
    )


# Запуск бота
async def main():
    logging.info("Бот запускается...")
    
    # Удаляем старые необработанные обновления
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```
