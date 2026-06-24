"""
Скрипт для первичного заполнения базы данных начальными данными.

Запуск: python -m bot.utils.seed
"""

import asyncio
import logging

from sqlalchemy import select

from bot.database import async_session_factory, init_db
from bot.models import Category, Material

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed() -> None:
    """Заполняет БД начальными данными."""
    await init_db()

    async with async_session_factory() as session:
        # Проверяем, есть ли уже данные
        result = await session.execute(select(Category))
        existing = result.scalars().all()
        if existing:
            logger.info("База данных уже содержит данные. Пропускаем seed.")
            return

        # Создаём 4 раздела
        categories_data = [
            {"title": "📹 OBS", "description": "Настройка OBS Studio, плагины, стрим, VDO.Ninja", "position": 0},
            {"title": "📁 Файлы", "description": "Работа с файлами, загрузка контента, хранение материалов", "position": 1},
            {"title": "🌐 Платформы", "description": "Работа на различных вебкам-платформах", "position": 2},
            {"title": "💬 Общение с мемберами", "description": "Скрипты общения, ведение шоу, привлечение и удержание", "position": 3},
        ]

        categories = []
        for cat_data in categories_data:
            category = Category(**cat_data)
            session.add(category)
            categories.append(category)

        await session.flush()  # Чтобы получить ID

        # Материал для раздела OBS (из существующего файла)
        obs_content = (
            "Качаем OBS по ссылке ниже, устанавливаем по дефолтному расположению которое предлагает сам установщик\n\n"
            "https://obsproject.com/\n\n"
            "Затем нам надо установить плагин мульти стрима, дабы наш стрим проходил сразу на нескольких площадках.\n\n"
            "❗️ОБЯЗАТЕЛЬНО❗️\n"
            "⚠️ ПЕРЕД УСТАНОВКОЙ ДОЛЖЕН БЫТЬ ПОЛНОСТЬЮ ЗАКРЫТ OBS, ДАЖЕ ИЗ ПАНЕЛИ ЗАДАЧ.\n"
            "ПУТЬ ФАЙЛОВ НЕ МЕНЯЙТЕ, УСТАНОВИТЬСЯ КУДА НАДО ⚠️\n\n"
            "Установщик плагина: obs-multi-rtmp-0.7.3.0-windows-x64-Installer.exe\n\n"
            "Выставляем в настройках OBS все как на картинке\n"
            "❗️ОБЯЗАТЕЛЬНО❗️\n"
            "⚠️После каждого действия в правом нижнем углу надо нажимать кнопку \"Применить\"⚠️\n"
            "⚠️А ТАК ЖЕ ПОЛЗУНКИ МИКРОФОНА И ЗВУКА РАБ. СТОЛА ДОЛЖНЫ БЫТЬ ВЫТЯНУТЫ ВНИЗ⚠️\n\n"
            "Затем добавляем источник браузера, дабы сделать сцену где модель будет передавать картинку с камеры своего телефона\n\n"
            "❗️ОБЯЗАТЕЛЬНО❗️\n"
            "⚠️НЕ ЗАБЫВАЙТЕ ВКЛЮЧАТЬ ФУНКЦИЮ \"ПЕРЕДАЧА АУДИО ЧЕРЕЗ OBS\" ИНАЧЕ НА СТРИМЕ БУДЕТ СЛЫШНО НЕ МОДЕЛЬ, А ВАС⚠️\n\n"
            "Чтобы добавить изображение с телефона модели нам нужно скиннуть им данный сайт.\n"
            "https://vdo.ninja/  - ОБЫЧНАЯ ССЫЛКА\n"
            "https://proxy.vdo.ninja/  - ССЫЛКА ЕСЛИ ИЗОБРАЖЕНИЕ ЖУТКО ЛАГАЕТ И ШАКАЛИТ КАЧЕСТВО\n\n"
            "Где в дальнейшем модель скинет нам ссылку передачи изображения.\n\n"
            "❗️МОДЕЛЬ ДОЛЖНА СКОПИРОВАТЬ ССЫЛКУ, ОТКРЫТЬ САФАРИ ИЛИ ЖЕ ДЕФОЛТНЫЙ БРАУЗЕР АНДРОИДА И ВСТАВИТЬ ТУДА ЭТУ ССЫЛКУ❗️\n\n"
            "Следуя белым стрелкам:\n"
            "Так модель должна скинуть ссылку вам\n\n"
            "Следуя красным стрелкам:\n"
            "Если у модели не передается изображение\n\n"
            "❗️ОБЯЗАТЕЛЬНО ❗️\n"
            "⚠️ У МОДЕЛИ ДОЛЖЕН БЫТЬ ОТКЛЮЧЕН ВПН И ВКЛЮЧЕН РЕЖИМ \"НЕБЕСПОКОИТЬ\" ⚠️"
        )

        materials_data = [
            {
                "category_id": categories[0].id,  # OBS
                "title": "Настройка OBS Studio",
                "content": obs_content,
                "position": 0,
            },
            {
                "category_id": categories[0].id,  # OBS
                "title": "Установка плагина мульти-стрима",
                "content": "Установка плагина obs-multi-rtmp для одновременного стрима на нескольких площадках.\n\n"
                           "1. Скачайте плагин obs-multi-rtmp-0.7.3.0-windows-x64-Installer.exe\n"
                           "2. Перед установкой полностью закройте OBS (даже из панели задач)\n"
                           "3. Запустите установщик, путь не меняйте\n"
                           "4. После установки откройте OBS и настройте несколько RTMP-серверов",
                "position": 1,
            },
            {
                "category_id": categories[0].id,  # OBS
                "title": "Настройка VDO.Ninja для видео с телефона",
                "content": "VDO.Ninja позволяет передавать видео с камеры телефона модели в OBS.\n\n"
                           "1. Отправьте модели ссылку: https://vdo.ninja/\n"
                           "2. Если изображение лагает, используйте: https://proxy.vdo.ninja/\n"
                           "3. Модель должна открыть ссылку в Safari или браузере Android\n"
                           "4. Модель копирует ссылку передачи изображения и отправляет вам\n"
                           "5. В OBS добавьте источник браузера и вставьте полученную ссылку\n\n"
                           "⚠️ У модели должен быть отключен ВПН и включен режим \"Не беспокоить\"",
                "position": 2,
            },
        ]

        for mat_data in materials_data:
            material = Material(**mat_data)
            session.add(material)

        await session.commit()
        logger.info("✅ База данных успешно заполнена начальными данными!")


if __name__ == "__main__":
    asyncio.run(seed())
