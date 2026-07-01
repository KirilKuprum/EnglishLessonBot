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

@dp.message(Command("encard"))
async def cmd_encard(message: Message):
    if client is None:
        await message.answer("ШІ сервіс не налаштований.")
        return

    try:
        prompt = PromptBuilder.simplePrompt()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        text = match.group(0) if match else response.text
        cards = json.loads(text)
        
        db_item = {
            'user_id': str(message.chat.id),
            'current_cards': cards,
            'status': 'pending',
            'current_index': 0
        }
        test_db.put_item(db_item)

        words_text = "**5:**\n\n"
        for i, card in enumerate(cards, 1):
            q = card.get('question') or card.get('word') or "Hello"
            a = card.get('answer') or card.get('translation') or "Привіт"
            words_text += f"{i}. **{q}** — {a}\n"

        await message.answer(words_text)
        await message.answer("Через годину готуйся...")
        
        run_date = datetime.now() + timedelta(seconds=10)
        scheduler.add_job(
            send_reminder, 
            'date', 
            run_date=run_date, 
            args=[message.chat.id, cards]
        )
        
        
    except Exception as err:
        print(f"Помилка: {err}")
        await message.answer("Сталася помилка при генерації карток.")


async def send_reminder(chat_id: int, cards: list):
    test_db.update_status(chat_id, 'active')
    
    if cards and len(cards) > 0:
        first_card = cards[0]
        
        question = first_card.get('question') or first_card.get('word') or "Не знайдено"
        answer = first_card.get('answer') or first_card.get('translation') or "Немає перекладу"
        
        await bot.send_message(chat_id, f"Слово для перекладу: **{question}**")
        
        print(f"DEBUG: Перша картка з бази: {first_card}")
    else:
        await bot.send_message(chat_id, "Помилка: масив карток порожній.")

@dp.message()
async def process_answer(message: Message):
    user_data = test_db.get_item(message.chat.id)
    
    if user_data and user_data.get('status') == 'active':
        cards = user_data['current_cards']
        idx = user_data.get('current_index', 0)

        if idx >= len(cards):
            await message.answer("Тест вже завершено.")
            test_db.update_status(message.chat.id, 'finished')
            return

        current_card = cards[idx]
        correct_answer = (current_card.get('answer') or current_card.get('translation') or "").lower().strip()
        user_answer = message.text.lower().strip()

        if user_answer == correct_answer:
            await message.answer("Допустим")
            test_db.update_stats(message.chat.id, True)
        else:
            await message.answer(f"Отказано. Вот: {correct_answer}")
            test_db.update_stats(message.chat.id, False)
            
        next_idx = idx + 1
        if next_idx < len(cards):
            test_db.update_index(message.chat.id, next_idx)
            
            next_card = cards[next_idx]
            next_question = next_card.get('question') or next_card.get('word') or "Next word"
            await message.answer(f"Наступне слово ({next_idx + 1}/{len(cards)}):\n **{next_question}**")
        else:
            await message.answer("Тест завершено! Ви пройшли всі 5 слів.")

            test_db.update_status(message.chat.id, 'finished')
    else:
        await message.answer("Натисніть /encard, щоб почати тест.")



async def main():
    global bot, client, test_db

    load_dotenv()
    bot = auth_telegram()
    client = auth_gemini_api()
    test_db = auth_db()

    scheduler.start()
    
    print("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
