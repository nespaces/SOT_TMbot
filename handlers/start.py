"""Обработчики команды /start."""
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.helpers import is_admin
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start."""
    try:
        user_id = update.effective_user.id
        logger.info(f"Processing /start command for user {user_id}")

        # Clear any existing conversation data
        context.user_data.clear()
        context.chat_data.clear()

        base_message = (
            "👋 Привет! Я бот для поиска команды в Sea of Thieves.\n\n"
            "Используйте кнопки меню ниже:"
        )

        # Check if user is admin and add admin command if true
        if await is_admin(update, context):
            base_message += "\n/admin - Панель администратора"

        # Create keyboard with one row of three buttons
        keyboard = [
            [
                "Создать анкету",
                "Мои анкеты",
                "Отмена"
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False  # Keep keyboard visible
        )

        await update.message.reply_text(base_message, reply_markup=reply_markup)
        logger.info(f"Start command processed successfully for user {user_id}")

    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )
