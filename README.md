# Sea of Thieves Teammate Search Bot

Telegram бот для поиска команды в Sea of Thieves с выбором типа модерации (ручная/автоматическая).

## Функционал

- 🔍 Создание и управление объявлениями о поиске команды
- 🛡️ Два режима модерации: ручная и автоматическая
- 🤖 AI-powered проверка контента с использованием OpenAI
- 🌍 Поддержка нескольких серверных регионов
- 💬 Интеграция с Discord и Telegram для связи
- 👥 Гибкая система ролей и фракций
- 🚢 Выбор типа корабля и платформы

## Требования

- Python 3.11+
- Зависимости Python (установка через pip):
  - python-telegram-bot[all,job-queue]
  - sqlalchemy
  - python-dotenv
  - openai (опционально, для AI модерации)
  - psutil

## Установка и настройка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd sot-teammate-search-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и настройте следующие переменные окружения:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_IDS=123456,789012  # ID администраторов через запятую
MODERATION_CHANNEL_ID=-100123456789  # ID канала модерации
LISTINGS_CHANNEL_ID=-100987654321  # ID канала объявлений
OPENAI_API_KEY=your_openai_key  # Опционально, для AI модерации
```

4. Инициализируйте базу данных:
```bash
python -c "from models.database import init_db; init_db()"
```

5. Запустите бота:
```bash
python bot.py
```

## Структура проекта

```
├── bot.py                 # Главный файл бота
├── config.py             # Конфигурация и переменные окружения
├── models/               # Модели базы данных
│   ├── database.py      # Настройка SQLite
│   └── listing.py       # Модель объявления
├── handlers/            # Обработчики команд
│   ├── start.py        # Команда /start
│   ├── create.py       # Создание объявлений
│   ├── manage.py       # Управление объявлениями
│   ├── admin.py        # Админ-панель
│   └── moderation.py   # Модерация объявлений
└── utils/              # Вспомогательные модули
    ├── constants.py    # Константы
    ├── formatters.py   # Форматирование сообщений
    ├── keyboards.py    # Клавиатуры
    ├── ai_helper.py    # Интеграция с OpenAI
    └── backup.py       # Резервное копирование
```

## Использование

1. Начните диалог с ботом командой `/start`
2. Используйте команду `/create` для создания нового объявления
3. Управляйте своими объявлениями через `/manage`
4. Администраторы могут использовать `/admin` для доступа к панели управления

## Резервное копирование

Бот поддерживает автоматическое резервное копирование:
- База данных: `utils/backup.py`
- Файлы проекта: `utils/backup_files.py`

## Вклад в проект

1. Создайте форк репозитория
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте изменения в форк (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## Лицензия

[MIT License](LICENSE)
