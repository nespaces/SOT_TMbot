"""Обработчики админских команд."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from config import config
from utils.helpers import is_admin

logger = logging.getLogger(__name__)

# Admin command states
MODERATION_SETTINGS = 1

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /admin."""
    # End current conversation if any
    return_value = ConversationHandler.END
    if context.user_data.get('conversation_key'):
        del context.user_data['conversation_key']

    # Clear any existing conversation data
    context.user_data.clear()
    context.chat_data.clear()

    # Check if user is admin
    if not await is_admin(update, context):
        await update.message.reply_text("У вас нет прав для использования этой команды.")
        return ConversationHandler.END

    # Create keyboard for moderation settings
    keyboard = [
        [
            InlineKeyboardButton("Автомодерация", callback_data="admin_mod_auto"),
            InlineKeyboardButton("Ручная модерация", callback_data="admin_mod_manual")
        ],
        [
            InlineKeyboardButton("🗑 Очистить все объявления", callback_data="admin_clear_all")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get current moderation type
    current_type = context.bot_data.get('moderation_type', 'manual')
    await update.message.reply_text(
        f"🛠 Панель администратора\n\n"
        f"Текущий режим модерации: {'Автоматический' if current_type == 'auto' else 'Ручной'}\n\n"
        f"Выберите режим модерации объявлений:",
        reply_markup=reply_markup
    )
    return MODERATION_SETTINGS

async def handle_moderation_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора режима модерации."""
    query = update.callback_query
    await query.answer()

    # Check if user is admin
    if update.effective_user.id not in config.ADMIN_IDS:
        await query.message.reply_text("У вас нет прав для использования этой команды.")
        return ConversationHandler.END

    try:
        mod_type = query.data.replace('admin_mod_', '')
        if mod_type not in ['auto', 'manual']:
            await query.message.reply_text("Некорректный выбор режима модерации.")
            return ConversationHandler.END

        # Save moderation type to context
        context.bot_data['moderation_type'] = mod_type

        # Update message to show current settings
        await query.message.edit_text(
            f"✅ Настройки обновлены\n\n"
            f"Текущий режим модерации: {'Автоматический' if mod_type == 'auto' else 'Ручной'}\n\n"
            f"Используйте /admin для изменения настроек."
        )
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error in handle_moderation_settings: {e}")
        await query.message.reply_text(
            "Произошла ошибка при обновлении настроек. Попробуйте позже."
        )
        return ConversationHandler.END

async def handle_clear_all_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка всех объявлений."""
    query = update.callback_query
    await query.answer()

    if not await is_admin(update, context):
        await query.message.reply_text("У вас нет прав для использования этой команды.")
        return

    try:
        from models.database import session_scope
        from models.listing import Listing
        from sqlalchemy import text

        with session_scope() as session:
            # Удаляем все записи из таблицы
            session.query(Listing).delete()
            # Сбрасываем автоинкремент
            session.execute(text("ALTER SEQUENCE listings_id_seq RESTART WITH 1"))

        await query.message.edit_text(
            "✅ Все объявления успешно удалены.\n"
            "Следующее созданное объявление будет иметь ID 1.\n\n"
            "Используйте /admin для возврата в панель администратора."
        )

    except Exception as e:
        logger.error(f"Error in handle_clear_all_listings: {e}")
        await query.message.reply_text(
            "Произошла ошибка при очистке объявлений. Попробуйте позже."
        )


async def handle_admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button press in admin panel."""
    query = update.callback_query
    await query.answer()

    if not await is_admin(update, context):
        await query.message.reply_text("У вас нет прав для использования этой команды.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Автомодерация", callback_data="admin_mod_auto"),
            InlineKeyboardButton("Ручная модерация", callback_data="admin_mod_manual")
        ],
        [
            InlineKeyboardButton("🗑 Очистить все объявления", callback_data="admin_clear_all")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    current_type = context.bot_data.get('moderation_type', 'manual')
    await query.message.edit_text(
        f"🛠 Панель администратора\n\n"
        f"Текущий режим модерации: {'Автоматический' if current_type == 'auto' else 'Ручной'}\n\n"
        f"Выберите режим модерации объявлений:",
        reply_markup=reply_markup
    )
    return MODERATION_SETTINGS

from utils.helpers import is_admin