from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, event
from sqlalchemy.orm import validates
from models.database import Base
import logging
import re

logger = logging.getLogger(__name__)

class Listing(Base):
    __tablename__ = 'listings'

    id = Column(Integer, primary_key=True)  # SQLite will auto-increment
    user_id = Column(Integer, nullable=False)  # Changed from BigInteger to Integer for SQLite
    nickname = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    experience = Column(Integer, nullable=False)
    role = Column(String(50), nullable=False)
    faction = Column(String(50), nullable=False)
    server = Column(String(20), nullable=False)
    ship_type = Column(String(20), nullable=False)
    platform = Column(String(20), nullable=False)
    additional_info = Column(Text)
    contacts = Column(String(200), nullable=False)
    search_type = Column(String(20), nullable=False)
    search_goal = Column(String(20), nullable=False)
    moderation_type = Column(String(20), default='manual')  # 'manual' or 'auto'
    status = Column(String(20), default='pending')
    rejection_reason = Column(String(200))  # For storing rejection reasons
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)  # SQLite will store as 0/1
    message_id = Column(Integer)

    def __repr__(self):
        return f"<Listing(id={self.id}, user_id={self.user_id}, nickname='{self.nickname}')>"

    @validates('contacts', 'additional_info')
    def validate_text_fields(self, key, value):
        """Валидация текстовых полей."""
        if value is None:
            value = ""

        # Конвертируем в строку если пришел другой тип
        value = str(value).strip()

        # Нормализуем пробелы
        value = ' '.join(value.split())

        max_lengths = {
            'contacts': 200,
            'additional_info': 500
        }

        if key in max_lengths and len(value) > max_lengths[key]:
            raise ValueError(f"{key.capitalize()} слишком длинный (максимум {max_lengths[key]} символов)")

        if key == 'contacts':
            # Проверяем наличие хотя бы одного способа связи
            if not any(pattern in value.lower() for pattern in ['@', 'discord', 'telegram', 'tel:', 'phone']):
                raise ValueError("Укажите хотя бы один способ связи (Telegram, Discord и т.д.)")

        if key == 'additional_info' and len(value) < 10:
            raise ValueError("Дополнительная информация должна содержать минимум 10 символов")

        return value

    @validates('age')
    def validate_age(self, key, age):
        """Валидация возраста."""
        try:
            age = int(age)
            if not (1 <= age <= 100):
                raise ValueError("Возраст должен быть от 1 до 100 лет")
            return age
        except (ValueError, TypeError):
            raise ValueError("Возраст должен быть числом от 1 до 100")

    @validates('experience')
    def validate_experience(self, key, experience):
        """Валидация опыта."""
        try:
            experience = int(experience)
            if experience < 0:
                raise ValueError("Опыт не может быть отрицательным")
            if experience > 100000:  # Разумное ограничение
                raise ValueError("Указано слишком большое значение опыта")
            return experience
        except (ValueError, TypeError):
            raise ValueError("Опыт должен быть положительным числом")

    @validates('search_type', 'search_goal', 'gender', 'role', 'faction', 'server', 'ship_type', 'platform', 'moderation_type')
    def validate_choice_fields(self, key, value):
        """Валидация полей с выбором из списка."""
        if not value or not str(value).strip():
            raise ValueError(f"Поле {key} не может быть пустым")

        value = str(value).strip()

        # Проверка значения moderation_type
        if key == 'moderation_type' and value not in ['manual', 'auto']:
            raise ValueError("Некорректный тип модерации")

        # Проверяем длину значения
        if len(value) > 50:
            raise ValueError(f"Значение поля {key} слишком длинное")

        return value

    def auto_moderate(self) -> tuple[bool, str]:
        """
        Автоматическая модерация объявления.
        Возвращает (approved: bool, reason: str)
        """
        # Проверка на спам/рекламу в дополнительной информации
        spam_keywords = ['buy', 'sell', 'cheap', 'discount', 'offer', 'price']
        if any(keyword in self.additional_info.lower() for keyword in spam_keywords):
            return False, "Обнаружены признаки рекламы или спама"

        # Проверка на корректность возраста
        if self.age < 13:
            return False, "Возраст должен быть не менее 13 лет"

        # Проверка на подозрительно большой опыт
        if self.experience > 50000:
            return False, "Подозрительно большое значение опыта"

        # Проверка на запрещенные слова в никнейме и контактах
        forbidden_words = ['admin', 'moderator', 'support']
        if any(word in self.nickname.lower() for word in forbidden_words):
            return False, "Никнейм содержит запрещенные слова"

        return True, ""

@event.listens_for(Listing, 'before_insert')
def check_active_listings(mapper, connection, target):
    """Проверяет наличие активных объявлений перед вставкой нового."""
    try:
        # Проверяем наличие активных объявлений для этого пользователя
        from sqlalchemy import select, func
        stmt = select(func.count()).select_from(Listing).where(
            Listing.user_id == target.user_id,
            Listing.is_active == 1,  # SQLite stores boolean as 0/1
            Listing.status != 'rejected'
        )
        result = connection.execute(stmt).scalar()

        if result > 0:
            logger.error(f"User {target.user_id} already has active listings: {result}")
            raise ValueError(
                "У вас уже есть активное объявление. "
                "Используйте /manage для управления существующими объявлениями."
            )

    except Exception as e:
        logger.error(f"Error in check_active_listings: {e}", exc_info=True)
        raise