from config import config
import re

def escape_markdown(text):
    """Escape Markdown special characters for MarkdownV2."""
    if text is None:
        return ""

    # Characters that need escaping in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    # First escape backslashes
    text = str(text).replace('\\', '\\\\')

    # Then escape other special characters
    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text

def format_listing_message(listing):
    """Format listing data into a readable message with proper MarkdownV2 escaping"""
    # Escape special characters in all text fields
    nickname = escape_markdown(listing.nickname)
    gender = escape_markdown(listing.gender)
    role = escape_markdown(listing.role)
    faction = escape_markdown(listing.faction)
    server = escape_markdown(listing.server)
    ship_type = escape_markdown(listing.ship_type)
    platform = escape_markdown(listing.platform)
    additional_info = escape_markdown(listing.additional_info)
    contacts = escape_markdown(listing.contacts)
    search_type = escape_markdown(listing.search_type)
    search_goal = escape_markdown(listing.search_goal)

    message = f"""
⚔️ ━━━━━━━━━━━━━━━ ⚔️

{config.CUSTOM_EMOJI_TYPE} *Тип объявления:* {search_type}
{config.CUSTOM_EMOJI_GOAL} *Цель поиска:* {search_goal}

👤 *Обо мне:*
{config.CUSTOM_EMOJI_NICKNAME} Никнейм: {nickname}
{config.CUSTOM_EMOJI_GENDER} Пол: {gender}
{config.CUSTOM_EMOJI_AGE} Возраст: {listing.age}
{config.CUSTOM_EMOJI_EXP} Опыт: {listing.experience} часов
{config.CUSTOM_EMOJI_ROLE} Роль: {role}
{config.CUSTOM_EMOJI_FACTION} Фракция: {faction}
{config.CUSTOM_EMOJI_SHIP} Тип корабля: {ship_type}
{config.CUSTOM_EMOJI_PLATFORM} Платформа: {platform}

🌐 *Сервер:* {server}

📋 *Дополнительная информация:*
{additional_info}

📱 *Связь:*
{contacts}

⚔️ ━━━━━━━━━━━━━━━ ⚔️

[Подать объявление](https://t\\.me/SOT\\_TMbot?start\\=create)
"""
    return message

def format_moderation_message(listing):
    """Format listing for moderation channel"""
    message = f"""
🔍 *Новое объявление на модерацию*

{format_listing_message(listing)}

*ID:* `{listing.id}`
"""
    return message