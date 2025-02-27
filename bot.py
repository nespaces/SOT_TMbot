import logging
import os
import sys
import fcntl
import signal
import psutil
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from config import config
from models.database import init_db
from handlers import (
    start_command, create_command, manage_command,
    handle_moderation_action, handle_listing_action,
    handle_search_type, handle_search_goal, handle_nickname,
    handle_gender, handle_age, handle_experience, handle_role,
    handle_faction, handle_server, handle_ship_type,
    handle_platform, handle_additional_info, handle_contacts,
    handle_contact_type, admin_command, handle_moderation_settings,
    handle_clear_all_listings, handle_admin_back,
    SEARCH_TYPE, SEARCH_GOAL, NICKNAME, GENDER, AGE,
    EXPERIENCE, ROLE, FACTION, SERVER, SHIP_TYPE,
    PLATFORM, ADDITIONAL_INFO, CONTACTS, MODERATION_SETTINGS
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed to DEBUG for more detailed logs
)
# Disable httpx and http11 logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore.http11').setLevel(logging.WARNING)
logging.getLogger('httpcore.connection').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Global variables
lock_file = '/tmp/telegram_bot.lock'
lock_fd = None
application = None

def signal_handler(signum, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {signum}")
    cleanup_and_exit()

def cleanup_and_exit():
    """Cleanup resources and exit."""
    global lock_fd, application
    logger.info("Starting cleanup...")

    # Stop the application if it's running
    if application:
        try:
            logger.info("Stopping application...")
            application.stop()
            application.shutdown()
            logger.info("Application stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping application: {e}")

    # Release the lock file
    if lock_fd is not None:
        try:
            logger.info("Releasing lock file...")
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
            if os.path.exists(lock_file):
                os.unlink(lock_file)
            logger.info("Lock file released")
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")

    logger.info("Cleanup completed")
    sys.exit(0)

def kill_existing_process(pid):
    """Kill the existing bot process."""
    try:
        if psutil.pid_exists(pid):
            logger.info(f"Attempting to terminate process {pid}")
            process = psutil.Process(pid)
            # Send SIGTERM first
            process.terminate()
            try:
                # Wait for the process to terminate
                process.wait(timeout=5)
                logger.info(f"Process {pid} terminated successfully")
                return True
            except psutil.TimeoutExpired:
                # If SIGTERM didn't work, try SIGKILL
                logger.warning(f"Process {pid} didn't respond to SIGTERM, sending SIGKILL")
                process.kill()
                process.wait(timeout=5)
                logger.info(f"Process {pid} killed successfully")
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError) as e:
        logger.error(f"Error killing process {pid}: {e}")
    return False

def acquire_lock():
    """Try to acquire a lock file to prevent multiple instances."""
    try:
        if os.path.exists(lock_file):
            logger.info(f"Lock file {lock_file} exists")
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                    if psutil.pid_exists(old_pid):
                        # Check if it's really our bot process
                        process = psutil.Process(old_pid)
                        if "python" in process.name() and "bot.py" in process.cmdline():
                            logger.warning(f"Bot is already running with PID: {old_pid}")
                            if not kill_existing_process(old_pid):
                                logger.error("Failed to terminate existing process")
                                return None
                        else:
                            logger.info(f"Process {old_pid} is not a bot instance")
                    else:
                        logger.info(f"Found stale lock file for non-existent PID: {old_pid}")

                    # Remove the lock file if it exists
                    try:
                        os.unlink(lock_file)
                        logger.info("Old lock file removed")
                    except OSError as e:
                        logger.error(f"Error removing lock file: {e}")
                        return None
            except (ValueError, IOError) as e:
                logger.error(f"Error reading lock file: {e}")
                try:
                    os.unlink(lock_file)
                except OSError:
                    pass

        # Create new lock file
        try:
            fd = os.open(lock_file, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.write(fd, str(os.getpid()).encode())
            logger.info(f"Lock acquired for PID {os.getpid()}")
            return fd
        except (OSError, IOError) as e:
            logger.error(f"Failed to create lock file: {e}")
            return None

    except Exception as e:
        logger.error(f"Unexpected error in acquire_lock: {e}")
        return None

async def cancel_command(update: Update, context):
    """Cancel and end the conversation."""
    try:
        if context:
            context.user_data.clear()
            context.chat_data.clear()
        await update.message.reply_text(
            'Действие отменено. Используйте команду "Создать анкету" для создания нового объявления.'
        )
    except Exception as e:
        logger.error(f"Error in cancel command: {e}")
        await update.message.reply_text(
            'Произошла ошибка. Пожалуйста, попробуйте позже.'
        )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    try:
        # Log the error to our logging system
        logger.error(f"Update {update} caused error {context.error}")

        if update and update.effective_message:
            text = "К сожалению, произошла ошибка при обработке запроса. Попробуйте позже."
            await update.effective_message.reply_text(text)
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

def main():
    """Start the bot."""
    global lock_fd, application

    try:
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Try to acquire lock
        lock_fd = acquire_lock()
        if lock_fd is None:
            logger.error("Could not acquire lock. Another instance might be running.")
            sys.exit(1)

        # Initialize database
        try:
            init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            cleanup_and_exit()

        # Create application
        application = ApplicationBuilder().token(config.BOT_TOKEN).build()

        # Create conversation handlers first
        create_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('create', create_command),
                MessageHandler(filters.TEXT & filters.Regex('^Создать анкету$'), create_command)
            ],
            states={
                SEARCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_type)],
                SEARCH_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_goal)],
                NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nickname)],
                GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gender)],
                AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
                EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_experience)],
                ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)],
                FACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_faction)],
                SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_server)],
                SHIP_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ship_type)],
                PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_platform)],
                CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contacts)],
                ADDITIONAL_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_additional_info)],
            },
            fallbacks=[
                CommandHandler('cancel', cancel_command),
                MessageHandler(filters.TEXT & filters.Regex('^Отмена$'), cancel_command)
            ],
            conversation_timeout=900
        )

        # Admin conversation handler
        admin_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(admin_command, pattern='^admin_start$')
            ],
            states={
                MODERATION_SETTINGS: [
                    CallbackQueryHandler(handle_moderation_settings, pattern='^admin_mod_'),
                    CallbackQueryHandler(handle_clear_all_listings, pattern='^admin_clear_all$'),
                    CallbackQueryHandler(handle_admin_back, pattern='^admin_back$')
                ]
            },
            fallbacks=[
                CallbackQueryHandler(cancel_command, pattern='^cancel$')
            ],
            conversation_timeout=300,
            per_message=True  # Enable per_message since all handlers are CallbackQueryHandler
        )

        # Add conversation handlers
        application.add_handler(create_conv_handler)
        application.add_handler(admin_conv_handler)

        # Add command handlers after conversation handlers
        command_handlers = [
            CommandHandler('start', start_command),
            CommandHandler('admin', admin_command),
            CommandHandler('manage', manage_command),
            MessageHandler(filters.TEXT & filters.Regex('^Создать анкету$'), create_command),
            MessageHandler(filters.TEXT & filters.Regex('^Мои анкеты$'), manage_command),
            MessageHandler(filters.TEXT & filters.Regex('^Отмена$'), cancel_command)
        ]

        for handler in command_handlers:
            application.add_handler(handler)
            logger.debug(f"Added command handler: {handler.__class__.__name__}")

        # Add callback query handlers last
        callback_handlers = [
            CallbackQueryHandler(handle_moderation_action, pattern='^mod_(approve|decline)_'),
            CallbackQueryHandler(handle_listing_action, pattern='^(delete|refresh)_'),
        ]

        for handler in callback_handlers:
            application.add_handler(handler)
            logger.debug(f"Added callback handler: {handler.__class__.__name__}")

        # Add error handler
        application.add_error_handler(error_handler)
        logger.debug("Added error handler")

        # Start bot
        logger.info("Starting bot")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
            close_loop=False
        )

    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        cleanup_and_exit()

if __name__ == '__main__':
    main()