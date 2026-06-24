from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import async_session_factory
from bot.keyboards.user_kb import (
    main_menu_keyboard,
    material_navigation_keyboard,
    materials_keyboard,
)
from bot.models import Category, Image, Material, UsageStats, User

router = Router()


async def register_or_update_user(
    session: AsyncSession, tg_id: int, username: str | None,
    first_name: str | None, last_name: str | None
) -> User:
    """Регистрирует нового пользователя или обновляет данные существующего."""
    result = await session.execute(
        select(User).where(User.telegram_id == tg_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
    else:
        user = User(
            telegram_id=tg_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)

    await session.commit()
    return user


async def log_stat(
    session: AsyncSession, user_id: int, material_id: int | None, action: str
) -> None:
    """Логирует действие пользователя."""
    stat = UsageStats(user_id=user_id, material_id=material_id, action=action)
    session.add(stat)
    await session.commit()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    async with async_session_factory() as session:
        user = await register_or_update_user(
            session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        # Проверяем, является ли пользователь админом из конфига
        from bot.config import ADMIN_IDS, WEB_APP_URL
        if message.from_user.id in ADMIN_IDS and not user.is_admin:
            user.is_admin = True
            await session.commit()

        # Получаем все категории
        result = await session.execute(
            select(Category).order_by(Category.position)
        )
        categories = result.scalars().all()

    await message.answer(
        f"👋 Добро пожаловать в бот обучения операторов!\n\n"
        f"Здесь вы найдёте все необходимые мануалы и инструкции для работы.\n\n"
        f"Выберите раздел:",
        reply_markup=main_menu_keyboard(categories, web_app_url=WEB_APP_URL)
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обработчик команды /menu."""
    from bot.config import WEB_APP_URL

    async with async_session_factory() as session:
        result = await session.execute(
            select(Category).order_by(Category.position)
        )
        categories = result.scalars().all()

    await message.answer(
        "🏠 Главное меню\n\nВыберите раздел:",
        reply_markup=main_menu_keyboard(categories, web_app_url=WEB_APP_URL)
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    """Возврат в главное меню."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Category).order_by(Category.position)
        )
        categories = result.scalars().all()

    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите раздел:",
        reply_markup=main_menu_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_category_materials(callback: CallbackQuery) -> None:
    """Показывает список материалов в выбранном разделе."""
    category_id = int(callback.data.split(":")[1])

    async with async_session_factory() as session:
        result = await session.execute(
            select(Material)
            .where(Material.category_id == category_id)
            .order_by(Material.position)
        )
        materials = result.scalars().all()

        cat_result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = cat_result.scalar_one_or_none()

        if not category:
            await callback.answer("Раздел не найден!", show_alert=True)
            return

    if not materials:
        await callback.message.edit_text(
            f"📁 {category.title}\n\n"
            f"В этом разделе пока нет материалов.",
            reply_markup=materials_keyboard([], category_id)
        )
    else:
        text = f"📁 {category.title}\n\nВыберите материал:"
        await callback.message.edit_text(
            text,
            reply_markup=materials_keyboard(materials, category_id)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("material:"))
async def show_material(callback: CallbackQuery) -> None:
    """Показывает содержимое материала."""
    material_id = int(callback.data.split(":")[1])

    async with async_session_factory() as session:
        result = await session.execute(
            select(Material).where(Material.id == material_id)
        )
        material = result.scalar_one_or_none()

        if not material:
            await callback.answer("Материал не найден!", show_alert=True)
            return

        # Получаем изображения
        img_result = await session.execute(
            select(Image)
            .where(Image.material_id == material_id)
            .order_by(Image.position)
        )
        images = img_result.scalars().all()

        # Логируем просмотр
        user_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            await log_stat(session, user.id, material_id, "view_material")

    # Отправляем текст материала
    text = f"📄 {material.title}\n\n{material.content}"

    # Telegram имеет лимит 4096 символов на сообщение
    if len(text) > 4000:
        # Разбиваем на части
        parts = []
        current = f"📄 {material.title}\n\n"
        remaining = material.content
        while remaining:
            # Ищем место для разбивки
            chunk = remaining[:4000 - len(current)]
            # Стараемся не разрывать посередине строки
            if "\n" in chunk:
                last_newline = chunk.rfind("\n")
                if last_newline > 0:
                    chunk = chunk[:last_newline]
            parts.append(current + chunk)
            remaining = remaining[len(chunk):]
            current = ""

        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part)
            else:
                await callback.message.answer(part)
    else:
        await callback.message.edit_text(text)

    # Отправляем изображения, если есть
    if images:
        media_group = []
        for img in images:
            caption = img.caption if img.caption else None
            media_group.append(
                (img.file_id, caption)
            )

        # Отправляем по одному (так как aiogram не поддерживает InputMedia в callback)
        for file_id, caption in media_group:
            await callback.message.answer_photo(
                photo=file_id,
                caption=caption
            )

    # Отправляем кнопки навигации
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=material_navigation_keyboard(material_id, material.category_id)
    )

    await callback.answer()
