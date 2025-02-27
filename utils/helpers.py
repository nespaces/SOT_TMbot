
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import config

logger = logging.getLogger(__name__)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user_id = update.effective_user.id
    
    # Сначала проверяем ADMIN_IDS
    if user_id in config.ADMIN_IDS:
        return True
        
    try:
        # Проверяем права в каналах
        for channel_id in [config.MODERATION_CHANNEL_ID, config.LISTINGS_CHANNEL_ID]:
            try:
                member = await context.bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=user_id
                )
                if member.status in ['creator', 'administrator']:
                    return True
            except Exception:
                continue
                
        return False
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False
