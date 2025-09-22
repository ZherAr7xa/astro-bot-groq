import os
import logging
import requests
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())

# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class UserState(StatesGroup):
    birth_data = State()
    question = State()

SAMPLE_NATAL = "Солнце в Деве, Луна в Раке, Асцендент в Скорпионе, Марс в 10-м доме в Козероге"

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "🌙 Добро пожаловать в пространство звёзд.\n\n"
        "Я помогу тебе раскрыть тайны твоей натальной карты и найти ответы, которые ищет твоя душа.\n\n"
        "Пришли, пожалуйста, дату, время и место рождения — я подготовлю для тебя персональный разбор.\n\n"
        "Формат: `ДД.ММ.ГГГГ ЧЧ:ММ Город`\n"
        "Например: `15.08.1990 14:30 Москва`",
        parse_mode="Markdown"
    )
    await UserState.birth_data.set()

@dp.message_handler(state=UserState.birth_data)
async def handle_birth_data(message: types.Message, state: FSMContext):
    await state.update_data(birth_data=message.text)
    await message.answer(
        "✨ Благодарю. Я уже чувствую энергию твоей карты...\n\n"
        "Теперь задай любой вопрос, который живёт в тебе:\n"
        "— Что мне важно понять о себе сейчас?\n"
        "— Как раскрыть мою силу в отношениях?\n"
        "— Что подсказывает мне моя Луна?\n\n"
        "Я слушаю тебя...",
        parse_mode="Markdown"
    )
    await UserState.question.set()

@dp.message_handler(state=UserState.question)
async def handle_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_question = message.text

    await message.answer("🕯️ Настраиваюсь на твою волну... Это займёт немного времени.", parse_mode="Markdown")

    prompt = f"""
Ты — профессиональный астролог с 15-летним стажем. Ты ведёшь личную консультацию.
Ты говоришь мягко, образно, с теплотой и глубоким уважением к судьбе клиента.
Ты НИКОГДА не упоминаешь слово "ИИ", "бот", "алгоритм", "система". Ты — человек.

Данные клиента: {SAMPLE_NATAL}
Вопрос клиента: "{user_question}"

Ответь так, будто ты сидишь напротив человека за чашкой травяного чая.
Используй личное обращение: "Ты", "Тебе", "Твоя душа".
Объясняй термины через метафоры и образы.
Добавь немного поэзии, но не перегружай.
Не используй списки. Пиши связным текстом — как поток сознания заботливого наставника.
Иногда начинай с: “Знаешь, когда я смотрю на твою карту...” или “Мне хочется сказать тебе...”
Заверши на тёплой ноте.
Ответ: 250-400 слов.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-telegram-bot-site.com",
        "X-Title": "AstroBot"
    }

    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Ты — астролог-практик, ведущий личные консультации. Ты чувствуешь энергии и говоришь от сердца."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.75,
        "max_tokens": 1024
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(data))
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"].strip()
            answer += "\n\n🌿 С любовью, Астера"
        else:
            answer = "🌙 К сожалению, звёзды пока молчат... Попробуй задать вопрос чуть позже."

        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await message.answer(answer[i:i+4000], parse_mode="Markdown")
        else:
            await message.answer(answer, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"🌙 Произошла звёздная помеха: {str(e)}")

    await state.finish()

if __name__ == '__main__':
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
