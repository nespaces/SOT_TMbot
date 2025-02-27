from telegram import Update, error as telegram
from telegram.ext import ContextTypes
from models.listing import Listing
from models.database import session_scope
from utils.formatters import format_listing_message
from utils.keyboards import create_listing_management_keyboard
from config import config
import logging

logger = logging.getLogger(__name__)

from utils.helpers import is_admin


async def handle_moderation_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle moderation actions (approve/decline) for listings."""
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest:
        logger.error("Failed to answer callback query - may be too old")
        return

    # Check if user is admin
    if not await is_admin(update, context):
        await query.answer("У вас нет прав для этого действия!", show_alert=True)
        return

    try:
        action, listing_id = query.data.split('_')[1:]
        listing_id = int(listing_id)

        with session_scope() as session:
            # Get listing from database
            listing = session.query(Listing).filter_by(id=listing_id).first()
            if not listing:
                await query.answer("Объявление не найдено!", show_alert=True)
                return

            # Skip moderation if listing was auto-approved
            if listing.moderation_type == 'auto' and listing.status == 'approved':
                await query.answer("Это объявление было автоматически одобрено", show_alert=True)
                return

            try:
                if action == "approve":
                    listing.status = "approved"
                    # Post to listings channel
                    message = await context.bot.send_message(
                        chat_id=config.LISTINGS_CHANNEL_ID,
                        text=format_listing_message(listing),
                        parse_mode='Markdown',
                        reply_markup=create_listing_management_keyboard(listing.id)
                    )
                    # Обновляем существующие сообщения
                    if listing.message_id:
                        try:
                            await context.bot.edit_message_text(
                                chat_id=config.LISTINGS_CHANNEL_ID,
                                message_id=listing.message_id,
                                text=format_listing_message(listing),
                                parse_mode='Markdown',
                                reply_markup=create_listing_management_keyboard(listing.id)
                            )
                        except telegram.error.BadRequest:
                            pass  # Игнорируем ошибки при обновлении старых сообщений
                    listing.message_id = message.message_id

                    # Notify user about approval
                    await context.bot.send_message(
                        chat_id=listing.user_id,
                        text="✅ Ваше объявление было одобрено и опубликовано!"
                    )
                    logger.info(f"Listing {listing_id} approved by admin {update.effective_user.id}")

                elif action == "decline":
                    listing.status = "rejected"
                    # Prompt admin for decline reason
                    decline_reasons = [
                        "Некорректно заполнены контактные данные",
                        "Неподходящая дополнительная информация",
                        "Нарушение правил сообщества",
                        "Недостоверная информация"
                    ]
                    reason = decline_reasons[0]  # Default reason

                    # Notify user with reason
                    await context.bot.send_message(
                        chat_id=listing.user_id,
                        text=f"❌ Ваше объявление было отклонено.\n\nПричина: {reason}\n\nВы можете создать новое объявление с помощью команды /create"
                    )
                    logger.info(f"Listing {listing_id} declined by admin {update.effective_user.id}")

                # Remove moderation buttons
                await query.edit_message_reply_markup(reply_markup=None)

            except telegram.error.BadRequest as e:
                logger.error(f"Telegram API error while processing moderation action: {e}")
                await query.answer("Ошибка при обработке действия. Попробуйте позже.", show_alert=True)

    except Exception as e:
        logger.error(f"Error in handle_moderation_action: {e}")
        await query.answer("Произошла ошибка при обработке действия.", show_alert=True)