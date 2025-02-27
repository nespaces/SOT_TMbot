"""Обработка создания объявления."""
from telegram import Update, ReplyKeyboardMarkup, error as telegram
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import logging

from models.listing import Listing
from models.database import session_scope
from utils.keyboards import (
    create_gender_keyboard, create_role_keyboard,
    create_faction_keyboard, create_server_keyboard,
    create_ship_keyboard, create_platform_keyboard,
    create_search_type_keyboard, create_search_goal_keyboard,
    create_moderation_keyboard, create_listing_management_keyboard,
    create_contact_type_keyboard
)
from utils.formatters import format_moderation_message, format_listing_message
from utils.constants import (
    SEARCH_TYPES, SEARCH_GOALS, GENDERS, ROLES, FACTIONS,
    SERVERS, SHIP_TYPES, PLATFORMS
)
from config import config

logger = logging.getLogger(__name__)

# State definitions
(
    SEARCH_TYPE, SEARCH_GOAL, NICKNAME, GENDER, AGE,
    EXPERIENCE, ROLE, FACTION, SERVER, SHIP_TYPE,
    PLATFORM, CONTACTS, ADDITIONAL_INFO
) = range(13)

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания объявления."""
    try:
        user_id = update.effective_user.id
        logger.info(f"Starting listing creation for user {user_id}")

        # Clear any existing conversation data
        context.user_data.clear()

        # Reset conversation state
        if 'conversation_started' in context.user_data:
            del context.user_data['conversation_started']
        context.chat_data.clear()

        # Quick check for active listings
        with session_scope() as session:
            active_listing = session.query(Listing).filter(
                Listing.user_id == user_id,
                Listing.is_active == True,
                Listing.status == 'approved',
                Listing.message_id.isnot(None)
            ).first()

            if active_listing:
                logger.info(f"User {user_id} already has active listing")
                await update.message.reply_text(
                    "У вас уже есть активное объявление. Используйте /manage для управления существующими объявлениями."
                )
                return ConversationHandler.END

        # Start with search type selection
        keyboard = create_search_type_keyboard()
        logger.debug(f"Created search type keyboard for user {user_id}")

        await update.message.reply_text(
            "Давайте создадим новое объявление! Для начала, выберите тип поиска:",
            reply_markup=keyboard
        )
        return SEARCH_TYPE

    except Exception as e:
        logger.error(f"Error in create_command: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при создании объявления. Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END

async def handle_search_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа поиска."""
    try:
        selected_type = update.message.text
        search_type = None
        
        for type_, data in SEARCH_TYPES.items():
            if data.get("name") == selected_type:
                search_type = type_
                break
                
        if not search_type:
            await update.message.reply_text("Пожалуйста, выберите корректный тип поиска.")
            return SEARCH_TYPE

        context.user_data['search_type'] = search_type
        context.user_data['expires_at'] = datetime.utcnow() + timedelta(
            days=SEARCH_TYPES[search_type]['duration_days']
        )

        keyboard = create_search_goal_keyboard()
        await update.message.reply_text(
            "Выберите цель поиска:",
            reply_markup=keyboard
        )
        return SEARCH_GOAL

    except Exception as e:
        logger.error(f"Error in handle_search_type: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново с /create"
        )
        return ConversationHandler.END

async def handle_search_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора цели поиска."""
    try:
        search_goal = update.message.text
        if search_goal not in SEARCH_GOALS:
            await update.message.reply_text("Пожалуйста, выберите цель поиска из предложенных вариантов.")
            return SEARCH_GOAL

        context.user_data['search_goal'] = search_goal
        await update.message.reply_text("Отлично! Теперь введите ваш никнейм:")
        return NICKNAME

    except Exception as e:
        logger.error(f"Error in handle_search_goal: {e}", exc_info=True)
        if query and query.message:
            await query.message.reply_text(
                "Произошла ошибка при выборе цели. Пожалуйста, начните заново с /create"
            )
        return ConversationHandler.END

async def handle_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода никнейма."""
    try:
        nickname = update.message.text.strip()
        if len(nickname) > 100:
            await update.message.reply_text(
                "Никнейм слишком длинный (максимум 100 символов). Пожалуйста, введите более короткий никнейм:"
            )
            return NICKNAME

        # Save to context
        context.user_data['nickname'] = nickname

        # Move to next step
        keyboard = create_gender_keyboard()
        await update.message.reply_text(
            "Выберите ваш пол:",
            reply_markup=keyboard
        )
        return GENDER

    except Exception as e:
        logger.error(f"Error in handle_nickname: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново с /create"
        )
        return ConversationHandler.END

async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пола."""
    try:
        gender = update.message.text
        if gender not in GENDERS:
            await update.message.reply_text("Пожалуйста, выберите пол из предложенных вариантов.")
            return GENDER

        context.user_data['gender'] = gender
        await update.message.reply_text("Введите ваш возраст (числом):")
        return AGE

    except Exception as e:
        logger.error(f"Error in handle_gender: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода возраста."""
    try:
        age = int(update.message.text.strip())
        if not (1 <= age <= 100):
            raise ValueError("Age out of range")
    except (ValueError, TypeError):
        await update.message.reply_text(
            "Пожалуйста, введите корректный возраст (число от 1 до 100):"
        )
        return AGE

    context.user_data['age'] = age
    await update.message.reply_text("Введите ваш опыт в игре (в часах):")
    return EXPERIENCE

async def handle_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода игрового опыта."""
    try:
        experience = int(update.message.text.strip())
        if experience < 0:
            raise ValueError("Negative experience")
        if experience > 100000:  # Разумное ограничение
            raise ValueError("Too high experience value")
    except (ValueError, TypeError):
        await update.message.reply_text(
            "Пожалуйста, введите корректное количество часов (положительное число):"
        )
        return EXPERIENCE

    context.user_data['experience'] = experience
    await update.message.reply_text(
        "Выберите вашу роль на корабле:",
        reply_markup=create_role_keyboard()
    )
    return ROLE

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора роли."""
    try:
        role = update.message.text
        if role not in ROLES:
            await update.message.reply_text("Пожалуйста, выберите роль из предложенных вариантов.")
            return ROLE

        context.user_data['role'] = role
        await update.message.reply_text(
            "Выберите вашу фракцию:",
            reply_markup=create_faction_keyboard()
        )
        return FACTION

    except Exception as e:
        logger.error(f"Error in handle_role: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_faction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора фракции."""
    try:
        faction = update.message.text
        if faction not in FACTIONS:
            await update.message.reply_text("Пожалуйста, выберите фракцию из предложенных вариантов.")
            return FACTION

        context.user_data['faction'] = faction
        await update.message.reply_text(
            "Выберите сервер:",
            reply_markup=create_server_keyboard()
        )
        return SERVER

    except Exception as e:
        logger.error(f"Error in handle_faction: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора сервера."""
    try:
        server = update.message.text
        if server not in SERVERS:
            await update.message.reply_text("Пожалуйста, выберите сервер из предложенных вариантов.")
            return SERVER

        context.user_data['server'] = server
        await update.message.reply_text(
            "Выберите тип корабля:",
            reply_markup=create_ship_keyboard()
        )
        return SHIP_TYPE

    except Exception as e:
        logger.error(f"Error in handle_server: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_ship_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа корабля."""
    try:
        ship_type = update.message.text
        if ship_type not in SHIP_TYPES:
            await update.message.reply_text("Пожалуйста, выберите тип корабля из предложенных вариантов.")
            return SHIP_TYPE

        context.user_data['ship_type'] = ship_type
        await update.message.reply_text(
            "Выберите платформу:",
            reply_markup=create_platform_keyboard()
        )
        return PLATFORM

    except Exception as e:
        logger.error(f"Error in handle_ship_type: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора платформы."""
    try:
        platform = update.message.text
        if platform not in PLATFORMS:
            await update.message.reply_text("Пожалуйста, выберите платформу из предложенных вариантов.")
            return PLATFORM

        context.user_data['platform'] = platform
        keyboard = ReplyKeyboardMarkup([
            ["Telegram"],
            ["Discord"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "Выберите способ связи:",
            reply_markup=keyboard
        )
        return CONTACTS

    except Exception as e:
        logger.error(f"Error in handle_platform: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_contact_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа контакта."""
    try:
        contact_type = update.message.text.lower()
        if contact_type == "discord":
            context.user_data['awaiting_discord'] = True
            await update.message.reply_text(
                "Введите ваш Discord (например: username#1234):"
            )
            return CONTACTS
        elif contact_type == "telegram":
            username = update.effective_user.username
            if not username:
                await update.message.reply_text(
                    "❌ У вас не установлен username в Telegram. Пожалуйста, установите его в настройках Telegram или выберите другой способ связи."
                )
                return CONTACTS
            context.user_data['contacts'] = f"@{username}"
            await update.message.reply_text(
                "Введите дополнительную информацию (цель поиска, предпочтения и т.д.):"
            )
            return ADDITIONAL_INFO
        else:
            await update.message.reply_text("Пожалуйста, выберите корректный способ связи.")
            return CONTACTS

    except Exception as e:
        logger.error(f"Error in handle_contact_type: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните заново с /create")
        return ConversationHandler.END

async def handle_additional_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода дополнительной информации."""
    try:
        if not update.message or not update.message.text:
            return ADDITIONAL_INFO

        additional_info = update.message.text.strip()

        # Базовая валидация
        if not additional_info:
            await update.message.reply_text(
                "❗ Пожалуйста, введите дополнительную информацию о ваших целях и предпочтениях:\n"
                "Например: 'Ищу команду для прохождения Tall Tales' или 'Хочу фармить ФП'"
            )
            return ADDITIONAL_INFO

        if len(additional_info) < 10:
            await update.message.reply_text(
                "❗ Слишком короткое описание. Пожалуйста, добавьте больше деталей о том, что вы хотите делать в игре (минимум 10 символов)"
            )
            return ADDITIONAL_INFO

        if len(additional_info) > 500:
            await update.message.reply_text(
                "❗ Описание слишком длинное (максимум 500 символов). Пожалуйста, сократите текст."
            )
            return ADDITIONAL_INFO

        # Сохраняем информацию
        context.user_data['additional_info'] = additional_info
        logger.info(f"Saved additional info: {additional_info[:50]}...")

        # Переходим к созданию объявления
        user_id = update.effective_user.id
        expires_at = context.user_data.get('expires_at')
        if not expires_at or expires_at <= datetime.utcnow():
            expires_at = datetime.utcnow() + timedelta(days=7)

        # Подготавливаем данные для создания объявления
        user_data = context.user_data.copy()

        # Удаляем служебные поля, которые не должны попасть в модель
        fields_to_remove = ['contact_type', 'awaiting_discord']
        for field in fields_to_remove:
            user_data.pop(field, None)

        # Проверяем и устанавливаем контакты
        if not user_data.get('contacts'):
            context.user_data.clear()
            await update.message.reply_text("Ошибка: контактные данные не установлены. Используйте /create чтобы начать заново.")
            return ConversationHandler.END

        listing_data = {
            'user_id': user_id,
            'status': "pending",
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'is_active': True,
            'moderation_type': context.bot_data.get('moderation_type', 'manual'),
            **user_data
        }

        with session_scope() as session:
            listing = Listing(**listing_data)

            if listing.moderation_type == 'auto':
                listing.status = 'approved'
                session.add(listing)
                session.commit()

                try:
                    message = await context.bot.send_message(
                        chat_id=config.LISTINGS_CHANNEL_ID,
                        text=format_listing_message(listing),
                        parse_mode='MarkdownV2',
                        reply_markup=create_listing_management_keyboard(listing.id)
                    )
                    listing.message_id = message.message_id
                    session.commit()

                    await context.bot.send_message(
                        chat_id=user_id,
                        text="✅ Ваше объявление было автоматически одобрено и опубликовано!"
                    )
                    return ConversationHandler.END

                except telegram.error.BadRequest as e:
                    logger.error(f"Telegram API error for user {user_id}: {e}")
                    session.rollback()
                    await update.message.reply_text(
                        "❌ Ошибка при отправке объявления. Пожалуйста, попробуйте позже с /create"
                    )
                    return ConversationHandler.END

            else:
                session.add(listing)
                session.flush()

                try:
                    moderation_text = format_moderation_message(listing)
                    await context.bot.send_message(
                        chat_id=config.MODERATION_CHANNEL_ID,
                        text=moderation_text,
                        parse_mode='MarkdownV2',
                        reply_markup=create_moderation_keyboard(listing.id)
                    )
                    await update.message.reply_text(
                        "✅ Объявление создано и отправлено на модерацию!\n"
                        "Вы получите уведомление после проверки."
                    )

                    context.user_data.clear()
                    return ConversationHandler.END

                except telegram.error.BadRequest as e:
                    logger.error(f"Telegram API error for user {user_id}: {e}")
                    session.rollback()
                    await update.message.reply_text(
                        "❌ Ошибка при отправке объявления. Пожалуйста, попробуйте позже с /create"
                    )
                    return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error in handle_additional_info: {e}", exc_info=True)
        error_message = str(e)
        if "У вас уже есть активное объявление" in error_message:
            await update.message.reply_text(
                "❌ У вас уже есть активное объявление. Используйте /manage для управления существующими объявлениями."
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте ввести информацию еще раз:"
            )
            return ADDITIONAL_INFO

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка контактных данных."""
    try:
        if not update.message or not update.message.text:
            return CONTACTS

        contact_type = update.message.text.lower()
        user_id = update.effective_user.id

        if contact_type == "telegram":
            username = update.effective_user.username
            if not username:
                await update.message.reply_text(
                    "❗ У вас не установлен username в Telegram. Пожалуйста, установите его в настройках или выберите другой способ связи."
                )
                return CONTACTS
            context.user_data['contacts'] = f"@{username}"
            await update.message.reply_text(
                "Введите дополнительную информацию (цель поиска, предпочтения и т.д.):"
            )
            return ADDITIONAL_INFO
            
        elif contact_type == "discord":
            context.user_data['awaiting_discord'] = True
            await update.message.reply_text(
                "Введите ваш Discord (например: username#1234):"
            )
            return CONTACTS
            
        elif context.user_data.get('awaiting_discord'):
            discord_username = update.message.text.strip()
            context.user_data['awaiting_discord'] = False
            
            if not discord_username or len(discord_username) > 100:
                await update.message.reply_text(
                    "❗ Пожалуйста, введите корректный Discord (например: username#1234):"
                )
                return CONTACTS
            
            if not discord_username.lower().startswith('discord:'):
                discord_username = f"Discord: {discord_username}"
            
            context.user_data['contacts'] = discord_username
            context.user_data['contact_type'] = 'discord'
            
            await update.message.reply_text(
                "Введите дополнительную информацию (цель поиска, предпочтения и т.д.):"
            )
            return ADDITIONAL_INFO
            
        else:
            await update.message.reply_text("Пожалуйста, выберите корректный способ связи.")
            return CONTACTS

    except Exception as e:
        logger.error(f"Error in handle_contacts for user {update.effective_user.id}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении контактов. Пожалуйста, попробуйте еще раз:"
        )
        return CONTACTS

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def create_contact_type_keyboard():
    """Create contact type selection keyboard."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Telegram", callback_data="contact_telegram")],
        [InlineKeyboardButton("Discord", callback_data="contact_discord")]
    ])
    return keyboard