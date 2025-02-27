import os
from dataclasses import dataclass, field
from typing import List
import logging

logger = logging.getLogger(__name__)

def parse_admin_ids() -> List[int]:
    """Parse admin IDs from environment variable."""
    admin_ids_str = os.environ.get("ADMIN_IDS", "")
    try:
        if not admin_ids_str:
            logger.warning("ADMIN_IDS environment variable is not set")
            return []
        return [int(id_str) for id_str in admin_ids_str.split(",") if id_str.strip()]
    except ValueError as e:
        logger.error(f"Error parsing ADMIN_IDS: {e}")
        return []

def parse_int_env(env_var: str, default: int = 0) -> int:
    """Parse integer environment variable."""
    try:
        value = int(os.environ.get(env_var, str(default)))
        if not value:
            logger.warning(f"{env_var} is not set (value: {value})")
        return value
    except (TypeError, ValueError) as e:
        logger.error(f"Error parsing {env_var}: {e}")
        return default

@dataclass
class Config:
    """Bot configuration from environment variables."""
    BOT_TOKEN: str = field(default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN"))
    ADMIN_IDS: List[int] = field(default_factory=parse_admin_ids)
    MODERATION_CHANNEL_ID: int = field(default_factory=lambda: parse_int_env("MODERATION_CHANNEL_ID"))
    LISTINGS_CHANNEL_ID: int = field(default_factory=lambda: parse_int_env("LISTINGS_CHANNEL_ID"))
    DATABASE_URL: str = field(
        default_factory=lambda: 'sqlite:///bot.db'  # Changed to SQLite
    )
    CUSTOM_EMOJI_TYPE: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_TYPE", "🎯"))
    CUSTOM_EMOJI_GOAL: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_GOAL", "🎮"))
    CUSTOM_EMOJI_ABOUT: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_ABOUT", "ℹ️"))
    CUSTOM_EMOJI_NICKNAME: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_NICKNAME", "👤"))
    CUSTOM_EMOJI_GENDER: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_GENDER", "⚧"))
    CUSTOM_EMOJI_AGE: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_AGE", "🔢"))
    CUSTOM_EMOJI_EXP: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_EXP", "⭐"))
    CUSTOM_EMOJI_ROLE: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_ROLE", "🎭"))
    CUSTOM_EMOJI_FACTION: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_FACTION", "⚔️"))
    CUSTOM_EMOJI_SHIP: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_SHIP", "🚢"))
    CUSTOM_EMOJI_PLATFORM: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_PLATFORM", "🎮"))
    CUSTOM_EMOJI_SEPARATOR: str = field(default_factory=lambda: os.environ.get("CUSTOM_EMOJI_SEPARATOR", "⚔️"))

    def __post_init__(self):
        """Validate required configuration."""
        missing_vars = []

        if not self.BOT_TOKEN:
            missing_vars.append("TELEGRAM_BOT_TOKEN")

        if not self.MODERATION_CHANNEL_ID:
            missing_vars.append("MODERATION_CHANNEL_ID")

        if not self.LISTINGS_CHANNEL_ID:
            missing_vars.append("LISTINGS_CHANNEL_ID")

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        logger.info("Configuration loaded successfully")

# Create single instance
config = Config()