import asyncio
import json
import random
import requests
from os import getenv
from dotenv import load_dotenv
from PromptBuilder import PromptBuilder

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from google import genai

from PromptBuilder import PromptBuilder
from db import DataBase

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

import json
import re


scheduler = AsyncIOScheduler()
scheduler.start()

dp = Dispatcher()
client = None
bot = None
test_db = None

def auth_db():
    try:
        return DataBase(table_name="TestTable", region="us-east-1")
    except Exception as err:
        print(f"Помилка БД: {type(err)}: {err}")
        return None

def auth_telegram():
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN provided")
    return Bot(token=token)

def auth_gemini_api():
    api_key = getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY provided.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Помилка ініціалізації Gemini: {e}")
        return None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Іефке")


async def send_reminder(bot: Bot, chat_id: int, cards: list):
    await bot.send_message(chat_id, "Час перевірити знання! Ось ваші картки:")
    for card in cards:
        await bot.send_message(chat_id, f"Як перекласти: {card['question']}?")


@dp.message(Command("encard"))
async def cmd_encard(message: Message):
    if client is None:
        await message.answer("ШІ сервіс не налаштований.")
        return

    try:
        prompt = PromptBuilder.simplePrompt()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        text = response.text.replace("```json", "").replace("```", "").strip()
        cards = json.loads(text)
        
        run_date = datetime.now() + timedelta(seconds=10)
        scheduler.add_job(
            send_reminder, 
            'date', 
            run_date=run_date, 
            args=[bot, message.chat.id, cards]
        )
        
        await message.answer("Через годину готуйся...")
        
    except Exception as err:
        print(f"Помилка: {err}")
        await message.answer("Сталася помилка при генерації карток.")


async def main():
    global bot, client, test_db

    load_dotenv()
    bot = auth_telegram()
    client = auth_gemini_api()
    test_db = auth_db()

    print("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())