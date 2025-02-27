from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from utils.constants import (
    GENDERS, ROLES, FACTIONS, SERVERS,
    SHIP_TYPES, PLATFORMS, SEARCH_TYPES, SEARCH_GOALS
)
import logging

logger = logging.getLogger(__name__)

def create_grid_keyboard(items, prefix, row_width=3):
    """Создание клавиатуры с кнопками в сетке."""
    buttons = []
    row = []

    for item in items:
        callback_data = f"{prefix}_{item}"
        if len(callback_data.encode()) > 64:  # Telegram callback data limit
            logger.warning(f"Callback data too long: {callback_data}")
            continue

        row.append(InlineKeyboardButton(item, callback_data=callback_data))

        if len(row) == row_width:
            buttons.append(row)
            row = []

    if row:  # Добавляем оставшиеся кнопки
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)

def create_keyboard_from_list(items, row_width=3):
    """Создание ReplyKeyboard из списка."""
    buttons = []
    row = []
    for item in items:
        row.append(item)
        if len(row) == row_width:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

def create_search_type_keyboard():
    """Создание клавиатуры для выбора типа поиска."""
    buttons = []
    for type_, data in SEARCH_TYPES.items():
        button_text = str(data["name"]) if isinstance(data, dict) and "name" in data else str(type_)
        buttons.append(button_text)
    return create_keyboard_from_list(buttons)

def create_search_goal_keyboard():
    """Создание клавиатуры для выбора цели поиска."""
    return create_keyboard_from_list(SEARCH_GOALS)

def create_gender_keyboard():
    """Создание клавиатуры для выбора пола."""
    return create_keyboard_from_list(GENDERS)

def create_role_keyboard():
    """Создание клавиатуры для выбора роли."""
    return create_keyboard_from_list(ROLES)

def create_faction_keyboard():
    """Создание клавиатуры для выбора фракции."""
    return create_keyboard_from_list(FACTIONS)

def create_server_keyboard():
    """Создание клавиатуры для выбора сервера."""
    return create_keyboard_from_list(SERVERS)

def create_ship_keyboard():
    """Создание клавиатуры для выбора типа корабля."""
    return create_keyboard_from_list(SHIP_TYPES)

def create_platform_keyboard():
    """Создание клавиатуры для выбора платформы."""
    return create_keyboard_from_list(PLATFORMS)

def create_moderation_keyboard(listing_id):
    """Создание клавиатуры для модерации."""
    buttons = [[
        InlineKeyboardButton("✅ Принять", callback_data=f"mod_approve_{listing_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"mod_decline_{listing_id}")
    ]]
    return InlineKeyboardMarkup(buttons)

def create_listing_management_keyboard(listing_id):
    """Создание клавиатуры для управления объявлением."""
    buttons = [[
        InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{listing_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{listing_id}")
    ]]
    return InlineKeyboardMarkup(buttons)

def create_contact_type_keyboard():
    """Create contact type selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Telegram", callback_data="contact_telegram"),
            InlineKeyboardButton("Discord", callback_data="contact_discord"),
            InlineKeyboardButton("Голосовой чат", callback_data="contact_voice")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_main_menu_keyboard():
    """Create main menu keyboard."""
    keyboard = [
        [
            "/create 📝 Создать объявление",
            "/manage 📋 Мои объявления",
            "/cancel ❌ Отмена"
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)