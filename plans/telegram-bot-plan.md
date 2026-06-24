# Telegram Bot для обучения операторов вебкам-агентств

## 1. Общая архитектура

```mermaid
graph TB
    TG[Telegram Bot API] -->|Polling| Bot[Python Bot - aiogram 3.x]
    Bot --> Router[Роутеры]
    Router --> UserHandlers[Пользовательские хендлеры]
    Router --> AdminHandlers[Админ-хендлеры]
    Router --> StatsHandlers[Статистика]
    
    UserHandlers --> Categories[4 раздела]
    Categories --> Content[Материалы с текстом + изображения]
    
    AdminHandlers --> CRUD[CRUD операции]
    AdminHandlers --> ManageContent[Управление контентом]
    
    Bot --> DB[(PostgreSQL)]
    DB --> Models[SQLAlchemy Models]
    Models --> User[User]
    Models --> Category[Category]
    Models --> Material[Material]
    Models --> Image[Image]
    Models --> Stats[UsageStats]
```

## 2. Структура проекта

```
e:/Account BOT/
├── bot/
│   ├── __init__.py
│   ├── main.py                  # Точка входа, запуск бота
│   ├── config.py                # Конфигурация (токен, БД, админы)
│   ├── database.py              # Подключение к БД, сессии
│   ├── models.py                # SQLAlchemy модели
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── user.py              # Хендлеры для пользователей
│   │   ├── admin.py             # Хендлеры для админ-панели
│   │   └── stats.py             # Хендлеры статистики
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── user_kb.py           # Клавиатуры пользователя
│   │   └── admin_kb.py          # Клавиатуры админа
│   │
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── admin.py             # Middleware для проверки админа
│   │
│   └── utils/
│       ├── __init__.py
│       └── seed.py              # Скрипт для первичного заполнения БД
│
├── Coaching/
│   └── STEP 1 OBS/
│       └── OBS.txt              # Существующий файл с инструкцией
│
├── requirements.txt
├── runtime.txt                  # Для Railway/Render
├── Procfile                     # Для Railway/Render
└── plans/
    └── telegram-bot-plan.md     # Этот файл
```

## 3. Разделы (категории)

| # | Название раздела | Описание |
|---|-----------------|----------|
| 1 | 📹 **OBS** | Настройка OBS Studio, плагины, стрим, VDO.Ninja |
| 2 | 📁 **Файлы** | Работа с файлами, загрузка контента, хранение материалов |
| 3 | 🌐 **Платформы** | Работа на различных вебкам-платформах |
| 4 | 💬 **Общение с мемберами** | Скрипты общения, ведение шоу, привлечение и удержание |

## 4. Модели базы данных (PostgreSQL)

```mermaid
erDiagram
    User {
        int id PK
        bigint telegram_id UK
        varchar username
        varchar first_name
        varchar last_name
        bool is_admin
        datetime created_at
        datetime last_active
    }
    
    Category {
        int id PK
        varchar title
        varchar description
        int position
        datetime created_at
    }
    
    Material {
        int id PK
        int category_id FK
        varchar title
        text content
        int position
        datetime created_at
        datetime updated_at
    }
    
    Image {
        int id PK
        int material_id FK
        varchar file_id
        varchar caption
        int position
    }
    
    UsageStats {
        int id PK
        int user_id FK
        int material_id FK
        varchar action
        datetime timestamp
    }
    
    Category ||--o{ Material : contains
    Material ||--o{ Image : has
    User ||--o{ UsageStats : performs
    Material ||--o{ UsageStats : tracked
```

### Описание моделей:

- **User** — пользователи бота. `telegram_id` уникальный. `is_admin` — флаг администратора.
- **Category** — 4 раздела. `position` — порядок сортировки.
- **Material** — материалы внутри разделов. `content` — текст мануала. `position` — порядок внутри категории.
- **Image** — изображения, прикрепленные к материалу. `file_id` — Telegram file_id для быстрой отправки без перезагрузки. `position` — порядок отображения.
- **UsageStats** — логи действий пользователей (просмотр раздела, просмотр материала).

## 5. Логика работы бота

### 5.1 Пользовательский интерфейс

```mermaid
sequenceDiagram
    User->>Bot: /start
    Bot->>DB: Регистрация/обновление пользователя
    Bot->>User: Приветствие + главное меню (4 кнопки-раздела)
    
    User->>Bot: Выбор раздела (например "OBS")
    Bot->>DB: Запрос материалов раздела
    Bot->>User: Список материалов в разделе
    
    User->>Bot: Выбор материала
    Bot->>DB: Запрос контента + изображений + логирование
    Bot->>User: Текст мануала
    Bot->>User: Отправка изображений (если есть)
    Bot->>User: Кнопка "Назад" / "Главное меню"
```

### 5.2 Админ-панель

```mermaid
sequenceDiagram
    Admin->>Bot: /admin
    Bot->>DB: Проверка is_admin
    alt is_admin = True
        Bot->>Admin: Админ-меню
        Admin->>Bot: Управление разделами
        Admin->>Bot: Управление материалами
        Admin->>Bot: Добавление изображений к материалам
        Admin->>Bot: Просмотр статистики
    else is_admin = False
        Bot->>Admin: Доступ запрещен
    end
```

### 5.3 Команды бота

| Команда | Описание | Доступ |
|---------|----------|--------|
| `/start` | Запуск бота, регистрация | Все |
| `/menu` | Главное меню | Все |
| `/admin` | Админ-панель | Админы |
| `/stats` | Статистика (краткая) | Админы |

### 5.4 Админ-функции (в админ-панели)

- **Управление разделами**: создание, редактирование названия/описания, удаление, изменение порядка
- **Управление материалами**: создание, редактирование текста, удаление, изменение порядка внутри раздела
- **Управление изображениями**: добавление изображений к материалу (через отправку фото боту), удаление, изменение порядка
- **Просмотр статистики**: общее количество пользователей, просмотры по разделам, активность по дням
- **Назначение админов**: добавление/удаление администраторов (только для супер-админа)

## 6. Технические детали

### 6.1 Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Фреймворк | aiogram 3.x |
| База данных | PostgreSQL |
| ORM | SQLAlchemy 2.x + asyncpg |
| Хостинг | Railway.app или Render.com |

### 6.2 Конфигурация (через переменные окружения)

```
BOT_TOKEN=8894246405:AAHwbV8OAHk9uhuiJDGgGlSQO5GliBjA6A4
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
ADMIN_IDS=123456789,987654321  # Telegram ID админов через запятую
```

### 6.3 Зависимости (requirements.txt)

```
aiogram>=3.0.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.28.0
python-dotenv>=1.0.0
```

## 7. План деплоя на Railway/Render

### 7.1 Railway.app (рекомендуется)

1. Создать аккаунт на [Railway.app](https://railway.app)
2. Подключить GitHub репозиторий
3. Добавить PostgreSQL сервис (Railway предоставляет БД)
4. Добавить сервис из репозитория
5. Настроить переменные окружения
6. Railway автоматически определит `requirements.txt` и запустит бота
7. Использовать `Procfile` для указания команды запуска: `worker: python -m bot.main`

### 7.2 Render.com

1. Создать аккаунт на [Render.com](https://render.com)
2. Создать новый Web Service, подключить GitHub
3. Добавить PostgreSQL через Render Dashboard
4. Настроить Build Command: `pip install -r requirements.txt`
5. Start Command: `python -m bot.main`
6. Настроить переменные окружения

### 7.3 Важные моменты деплоя

- Бот использует **Polling** (не Webhook), так как на бесплатных тарифах Railway/Render нет статического IP для Webhook
- На Render бесплатный тариф "спит" после 15 минут бездействия — нужно использовать **Cron-job** (например, cron-job.org) для пингования раз в 10 минут, либо подключить платный тариф
- На Railway бесплатный тариф более стабилен для ботов

## 8. Пошаговый план реализации

### Шаг 1: Создание структуры проекта
- Создать папки `bot/`, `bot/handlers/`, `bot/keyboards/`, `bot/middlewares/`, `bot/utils/`
- Создать `__init__.py` во всех пакетах

### Шаг 2: Конфигурация и БД
- Создать `bot/config.py` с загрузкой переменных окружения
- Создать `bot/database.py` с подключением к PostgreSQL через SQLAlchemy async
- Создать `bot/models.py` с моделями User, Category, Material, Image, UsageStats

### Шаг 3: Ядро бота
- Создать `bot/main.py` — точка входа, инициализация бота и диспетчера
- Настроить middleware для админов

### Шаг 4: Пользовательские хендлеры
- `/start` — приветствие и регистрация
- `/menu` — главное меню с 4 разделами
- Просмотр материалов внутри раздела
- Отправка изображений вместе с текстом материала
- Кнопки навигации (назад, главное меню)

### Шаг 5: Админ-панель
- `/admin` — вход в админ-панель
- CRUD для разделов
- CRUD для материалов
- Добавление/удаление изображений к материалам
- Назначение админов

### Шаг 6: Статистика
- Логирование просмотров в UsageStats
- Команда `/stats` для админов
- Статистика по пользователям и материалам

### Шаг 7: Перенос контента
- Создать seed-скрипт для заполнения БД начальными данными
- Перенести содержимое OBS.txt в БД как первый материал раздела "OBS"

### Шаг 8: Деплой
- Создать `requirements.txt`, `runtime.txt`, `Procfile`
- Загрузить код на GitHub
- Настроить деплой на Railway.app

## 9. Безопасность

- Токен бота хранить только в переменных окружения, **не в коде**
- Админы определяются через `ADMIN_IDS` в env + флаг `is_admin` в БД
- Все SQL-запросы через ORM (защита от SQL-инъекций)
- Ограничение на длину сообщений Telegram (4096 символов) — разбивать длинные материалы
