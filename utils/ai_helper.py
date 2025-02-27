"""AI helper functions for the bot."""
import openai
import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def check_content(text: str) -> Tuple[bool, str]:
    """
    Проверяет контент на соответствие правилам с помощью ChatGPT.
    Returns: (is_valid, reason)
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                Ты модератор для игрового сообщества Sea of Thieves.
                Проверь текст на соответствие следующим правилам:
                1. Нет нецензурной лексики
                2. Нет дискриминации
                3. Нет спама или рекламы
                4. Текст относится к игре Sea of Thieves
                5. Нет личной информации кроме игровых контактов
                
                Ответь только true если текст соответствует правилам,
                или false и причину отказа если не соответствует.
                """},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        
        result = response.choices[0].message.content.lower()
        if result.startswith("true"):
            return True, ""
        else:
            reason = result.replace("false", "").strip()
            return False, reason

    except Exception as e:
        logger.error(f"Error in check_content: {e}")
        return True, "Ошибка проверки, пропускаем"

async def help_with_description(user_input: str) -> str:
    """
    Помогает пользователю составить описание для объявления.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                Ты помощник для игроков Sea of Thieves.
                Помоги дополнить или улучшить описание для поиска команды.
                Сохрани основную идею, но сделай текст более информативным.
                Используй не более 2-3 предложений.
                """},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error in help_with_description: {e}")
        return user_input
