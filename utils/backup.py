import os
import shutil
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

logger = logging.getLogger(__name__)

def create_backup():
    """Create a backup of the SQLite database."""
    try:
        # Create backups directory if it doesn't exist
        if not os.path.exists('backups'):
            os.makedirs('backups')

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/bot_{timestamp}.db'

        # Get the path to the SQLite database file
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot.db'))

        if os.path.exists(db_path):
            # Copy the database file
            shutil.copy2(db_path, backup_file)
            logger.info(f"Backup created successfully: {backup_file}")
            return backup_file
        else:
            logger.warning("Database file not found, no backup created")
            return None

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    create_backup()