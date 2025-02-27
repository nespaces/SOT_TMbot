from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import config
import logging
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

Base = declarative_base()

# Configure SQLite engine
database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot.db'))
engine = create_engine(
    f'sqlite:///{database_path}',
    connect_args={'check_same_thread': False},  # Allow multi-threading for SQLite
)

Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initialize database and create all tables."""
    try:
        from models.listing import Listing  # noqa: F401
        Base.metadata.create_all(engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise