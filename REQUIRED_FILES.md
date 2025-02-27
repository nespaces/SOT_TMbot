# Необходимые файлы для работы Telegram-бота

## Основные файлы
- `bot.py` - Главный файл запуска бота, содержит инициализацию и регистрацию всех обработчиков
- `config.py` - Конфигурация бота, работа с переменными окружения
- `main.py` - Точка входа в приложение

## Модели и база данных
- `models/__init__.py` - Инициализация моделей
- `models/database.py` - Настройка подключения к SQLite
- `models/listing.py` - Модель объявления
- `bot.db` - Файл базы данных SQLite

## Обработчики команд
- `handlers/__init__.py` - Экспорт всех обработчиков
- `handlers/start.py` - Обработка команды /start
- `handlers/create.py` - Создание объявления
- `handlers/manage.py` - Управление объявлениями
- `handlers/admin.py` - Админ-панель
- `handlers/moderation.py` - Модерация объявлений

## Утилиты
- `utils/__init__.py` - Инициализация утилит
- `utils/constants.py` - Константы (типы поиска, роли и т.д.)
- `utils/formatters.py` - Форматирование сообщений
- `utils/helpers.py` - Вспомогательные функции
- `utils/keyboards.py` - Клавиатуры для бота
- `utils/ai_helper.py` - Интеграция с OpenAI
- `utils/backup.py` - Резервное копирование БД
- `utils/backup_files.py` - Резервное копирование файлов

## Переменные окружения
Необходимые переменные окружения:
- `TELEGRAM_BOT_TOKEN` - Токен Telegram бота
- `ADMIN_IDS` - ID администраторов (через запятую)
- `MODERATION_CHANNEL_ID` - ID канала модерации
- `LISTINGS_CHANNEL_ID` - ID канала объявлений
- `OPENAI_API_KEY` - Ключ API OpenAI (опционально)

## Зависимости Python
Основные пакеты:
- python-telegram-bot[all,job-queue]
- sqlalchemy
- python-dotenv
- openai (опционально)

## Порядок запуска
1. Установить все зависимости
2. Настроить переменные окружения
3. Запустить бот командой `python bot.py`

## Резервное копирование
Для создания резервных копий используются скрипты:
- `utils/backup.py` - для БД (копирует файл SQLite)
- `utils/backup_files.py` - для файлов проекта