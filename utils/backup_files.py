import os
import shutil
from datetime import datetime
import logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

def create_files_backup():
    """Create a backup of all project files."""
    try:
        # Create backups directory if it doesn't exist
        if not os.path.exists('backups'):
            os.makedirs('backups')

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/files_backup_{timestamp}'

        # Files and directories to exclude
        exclude = {
            '__pycache__',
            '.git',
            '.upm',
            '.config',
            'venv',
            'backups',
            '.pytest_cache',
            '.replit',
            'poetry.lock',
            'replit.nix'
        }

        # Create backup directory
        os.makedirs(backup_dir)

        # Copy files and directories
        for item in os.listdir('.'):
            if item in exclude or item.startswith('.'):
                continue

            source = os.path.join('.', item)
            destination = os.path.join(backup_dir, item)

            if os.path.isdir(source):
                shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*exclude))
            else:
                shutil.copy2(source, destination)

        # Create archive
        archive_name = f'{backup_dir}.tar.gz'
        shutil.make_archive(backup_dir, 'gztar', backup_dir)

        # Remove temporary directory
        shutil.rmtree(backup_dir)

        logger.info(f"Files backup created successfully: {archive_name}")
        return archive_name

    except Exception as e:
        logger.error(f"Error creating files backup: {e}")
        return None

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    create_files_backup()
