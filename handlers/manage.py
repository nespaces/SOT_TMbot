"""Обработчики управления объявлениями."""
from telegram import Update, error as telegram_error
from telegram.ext import ContextTypes
from models.listing import Listing
from models.database import session_scope
from utils.formatters import format_listing_message
from utils.keyboards import create_listing_management_keyboard
from config import config
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

async def manage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /manage command to show user's active listings."""
    user_id = update.effective_user.id
    logger.info(f"Managing listings for user {user_id}")

    # Clear conversation state
    context.user_data.clear()

    try:
        with session_scope() as session:
            # Add debug logging
            logger.debug(f"Querying active listings for user {user_id}")

            # SQLite stores booleans as 0/1, so we need to be explicit in our comparison
            user_listings = session.query(Listing).filter(
                Listing.user_id == user_id,
                Listing.is_active == 1,  # SQLite boolean true is 1
                Listing.status == 'approved'
            ).all()

            # Log the results
            logger.debug(f"Found {len(user_listings)} active listings for user {user_id}")
            for listing in user_listings:
                logger.debug(f"Listing ID: {listing.id}, Status: {listing.status}, Active: {listing.is_active}")

            if not user_listings:
                await update.message.reply_text(
                    "У вас пока нет активных объявлений. Используйте команду /create чтобы создать новое!"
                )
                return

            for listing in user_listings:
                message_text = format_listing_message(listing)
                logger.debug(f"Formatted message for listing {listing.id}: {message_text[:100]}...")

                try:
                    await update.message.reply_text(
                        message_text,
                        parse_mode='MarkdownV2',  # Changed to MarkdownV2 for better compatibility
                        reply_markup=create_listing_management_keyboard(listing.id)
                    )
                    logger.debug(f"Successfully sent message for listing {listing.id}")
                except telegram_error.BadRequest as e:
                    logger.error(f"Failed to send listing {listing.id} to user {user_id}: {e}")
                    # Try sending without Markdown formatting if it fails
                    try:
                        await update.message.reply_text(
                            message_text,
                            reply_markup=create_listing_management_keyboard(listing.id)
                        )
                    except telegram_error.BadRequest as e:
                        logger.error(f"Failed to send listing without markdown: {e}")
                    continue

    except SQLAlchemyError as e:
        logger.error(f"Database error in manage command for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при получении списка объявлений. Пожалуйста, попробуйте через несколько минут."
        )
    except Exception as e:
        logger.error(f"Unexpected error in manage command for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при выполнении действия. Пожалуйста, попробуйте позже."
        )

async def handle_listing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle listing management actions (delete/refresh)."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    try:
        action, listing_id = query.data.split('_')
        listing_id = int(listing_id)

        if action == "refresh":
            with session_scope() as session:
                listing = session.query(Listing).filter_by(id=listing_id).first()
                if listing:
                    try:
                        # Проверяем существование сообщения в канале
                        try:
                            await context.bot.get_chat_message(
                                chat_id=config.LISTINGS_CHANNEL_ID,
                                message_id=listing.message_id
                            )
                        except telegram_error.BadRequest:
                            await query.message.reply_text("❌ Сообщение не найдено в канале")
                            # Сбрасываем message_id так как сообщение не существует
                            listing.message_id = None
                            session.commit()
                            return

                        # Сначала отправляем новое сообщение
                        new_message = await context.bot.send_message(
                            chat_id=config.LISTINGS_CHANNEL_ID,
                            text=format_listing_message(listing),
                            parse_mode='MarkdownV2' #Changed to MarkdownV2 for better compatibility
                        )

                        # После успешной отправки нового сообщения удаляем старое
                        if listing.message_id:
                            try:
                                await context.bot.delete_message(
                                    chat_id=config.LISTINGS_CHANNEL_ID,
                                    message_id=listing.message_id
                                )
                            except telegram_error.BadRequest:
                                logger.warning(f"Could not delete old message {listing.message_id}")

                        # Обновляем ID сообщения в базе данных
                        listing.message_id = new_message.message_id
                        session.commit()
                        await query.message.reply_text("✅ Объявление обновлено!")
                    except Exception as e:
                        logger.error(f"Error refreshing message: {e}")
                        await query.message.reply_text("❌ Не удалось обновить объявление")
                else:
                    await query.message.reply_text("❌ Объявление не найдено")

        elif action == "delete":
            with session_scope() as session:
                listing = session.query(Listing).filter_by(
                    id=listing_id,
                    user_id=user_id,
                    is_active=1  # SQLite boolean true is 1
                ).first()

                if not listing:
                    await query.message.reply_text(
                        "Объявление не найдено или уже было удалено."
                    )
                    return

                # Деактивируем объявление
                listing.is_active = 0  # SQLite boolean false is 0

                # Пытаемся удалить сообщение из канала объявлений
                if listing.message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=config.LISTINGS_CHANNEL_ID,
                            message_id=listing.message_id
                        )
                    except telegram_error.BadRequest as e:
                        logger.warning(f"Could not delete message from channel: {e}")

                # Пытаемся удалить сообщение с кнопками управления
                try:
                    await query.message.delete()
                except telegram_error.BadRequest as e:
                    logger.warning(f"Could not delete message with buttons: {e}")

                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="✅ Ваше объявление было успешно удалено!"
                    )
                except telegram_error.BadRequest as e:
                    logger.warning(f"Could not send confirmation message: {e}")

                session.commit()

    except SQLAlchemyError as e:
        logger.error(f"Database error in handle_listing_action for user {user_id}: {e}", exc_info=True)
        await query.message.reply_text(
            "Произошла ошибка при удалении объявления. Пожалуйста, попробуйте позже."
        )
    except Exception as e:
        logger.error(f"Unexpected error in handle_listing_action for user {user_id}: {e}", exc_info=True)
        await query.message.reply_text(
            "Произошла ошибка при выполнении действия. Пожалуйста, попробуйте позже."
        )