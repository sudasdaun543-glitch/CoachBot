from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ADMIN_IDS
from bot.database import async_session_factory
from bot.keyboards.admin_kb import (
    admin_category_actions_keyboard,
    admin_category_choice_keyboard,
    admin_confirm_delete_keyboard,
    admin_images_actions_keyboard,
    admin_main_keyboard,
    admin_material_actions_keyboard,
    admin_materials_list_keyboard,
    admin_categories_list_keyboard,
    admin_admins_keyboard,
)
from bot.keyboards.user_kb import main_menu_keyboard
from bot.models import Category, Image, Material, User

router = Router()


# ---- FSM Состояния ----

class AdminStates(StatesGroup):
    # Категории
    waiting_category_title = State()
    waiting_category_rename = State()
    # Материалы
    waiting_material_category = State()
    waiting_material_title = State()
    waiting_material_content = State()
    waiting_material_edit_text = State()
    # Изображения
    waiting_image_upload = State()
    # Админы
    waiting_admin_id = State()


# ---- Проверка админа ----

async def is_admin_user(tg_id: int) -> bool:
    """Проверяет, является ли пользователь админом."""
    if tg_id in ADMIN_IDS:
        return True
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == tg_id)
        )
        user = result.scalar_one_or_none()
        return user.is_admin if user else False


def admin_required(handler):
    """Декоратор для проверки прав админа."""
    async def wrapper(*args, **kwargs):
        # Определяем, откуда берём tg_id
        for arg in args:
            if isinstance(arg, (Message, CallbackQuery)):
                tg_id = arg.from_user.id
                if not await is_admin_user(tg_id):
                    if isinstance(arg, CallbackQuery):
                        await arg.answer("❌ У вас нет доступа!", show_alert=True)
                    else:
                        await arg.answer("❌ У вас нет доступа к этой команде.")
                    return
                break
        return await handler(*args, **kwargs)
    return wrapper


# ---- Команда /admin ----

@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Вход в админ-панель."""
    if not await is_admin_user(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "👑 Админ-панель\n\nВыберите действие:",
        reply_markup=admin_main_keyboard()
    )


# ---- Обработка нажатий админ-панели ----

@router.callback_query(F.data.startswith("admin:"))
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик всех admin callback'ов."""
    if not await is_admin_user(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return

    data = callback.data
    action = data.split(":")[1]

    # ---- Главное меню админки ----
    if action == "back":
        await callback.message.edit_text(
            "👑 Админ-панель\n\nВыберите действие:",
            reply_markup=admin_main_keyboard()
        )
        await callback.answer()
        return

    # ---- Управление разделами ----
    if action == "categories":
        async with async_session_factory() as session:
            result = await session.execute(
                select(Category).order_by(Category.position)
            )
            categories = result.scalars().all()

        await callback.message.edit_text(
            "📂 Управление разделами:",
            reply_markup=admin_categories_list_keyboard(categories)
        )
        await callback.answer()
        return

    if action == "create_cat":
        await state.set_state(AdminStates.waiting_category_title)
        await callback.message.edit_text(
            "Введите название нового раздела:"
        )
        await callback.answer()
        return

    if action.startswith("edit_cat:"):
        cat_id = int(data.split(":")[2])
        async with async_session_factory() as session:
            result = await session.execute(
                select(Category).where(Category.id == cat_id)
            )
            cat = result.scalar_one_or_none()
            if not cat:
                await callback.answer("Раздел не найден!", show_alert=True)
                return

        await callback.message.edit_text(
            f"📂 Раздел: {cat.title}\n"
            f"Описание: {cat.description or 'нет'}\n"
            f"Позиция: {cat.position}",
            reply_markup=admin_category_actions_keyboard(cat_id)
        )
        await callback.answer()
        return

    if action.startswith("rename_cat:"):
        cat_id = int(data.split(":")[2])
        await state.update_data(edit_cat_id=cat_id)
        await state.set_state(AdminStates.waiting_category_rename)
        await callback.message.edit_text(
            "Введите новое название раздела:"
        )
        await callback.answer()
        return

    if action.startswith("delete_cat:"):
        cat_id = int(data.split(":")[2])
        await callback.message.edit_text(
            "⚠️ Вы уверены, что хотите удалить этот раздел?\n"
            "Все материалы внутри также будут удалены!",
            reply_markup=admin_confirm_delete_keyboard("cat", cat_id)
        )
        await callback.answer()
        return

    # ---- Управление материалами ----
    if action == "materials":
        async with async_session_factory() as session:
            result = await session.execute(
                select(Category).order_by(Category.position)
            )
            categories = result.scalars().all()

        await callback.message.edit_text(
            "📄 Выберите раздел для просмотра материалов:",
            reply_markup=admin_category_choice_keyboard(categories)
        )
        await callback.answer()
        return

    if action.startswith("choose_cat_mat:"):
        cat_id = int(data.split(":")[2])
        async with async_session_factory() as session:
            result = await session.execute(
                select(Material)
                .where(Material.category_id == cat_id)
                .order_by(Material.position)
            )
            materials = result.scalars().all()

        await callback.message.edit_text(
            f"📄 Материалы в разделе:",
            reply_markup=admin_materials_list_keyboard(materials)
        )
        await callback.answer()
        return

    if action == "create_mat":
        async with async_session_factory() as session:
            result = await session.execute(
                select(Category).order_by(Category.position)
            )
            categories = result.scalars().all()

        await state.set_state(AdminStates.waiting_material_category)
        await callback.message.edit_text(
            "Выберите раздел для нового материала:",
            reply_markup=admin_category_choice_keyboard(categories)
        )
        await callback.answer()
        return

    if action.startswith("edit_mat:"):
        mat_id = int(data.split(":")[2])
        async with async_session_factory() as session:
            result = await session.execute(
                select(Material).where(Material.id == mat_id)
            )
            mat = result.scalar_one_or_none()
            if not mat:
                await callback.answer("Материал не найден!", show_alert=True)
                return

        await callback.message.edit_text(
            f"📄 Материал: {mat.title}\n\n"
            f"{mat.content[:500]}{'...' if len(mat.content) > 500 else ''}",
            reply_markup=admin_material_actions_keyboard(mat_id)
        )
        await callback.answer()
        return

    if action.startswith("edit_mat_text:"):
        mat_id = int(data.split(":")[2])
        await state.update_data(edit_mat_id=mat_id)
        await state.set_state(AdminStates.waiting_material_edit_text)
        await callback.message.edit_text(
            "Введите новый текст материала:"
        )
        await callback.answer()
        return

    if action.startswith("edit_mat_images:"):
        mat_id = int(data.split(":")[2])
        await state.update_data(edit_mat_images_id=mat_id)

        async with async_session_factory() as session:
            result = await session.execute(
                select(Image)
                .where(Image.material_id == mat_id)
                .order_by(Image.position)
            )
            images = result.scalars().all()

        text = f"🖼 Изображения материала:\n"
        if images:
            for i, img in enumerate(images, 1):
                text += f"{i}. {img.caption or 'без подписи'} (id: {img.id})\n"
        else:
            text += "Нет изображений\n"

        await callback.message.edit_text(
            text,
            reply_markup=admin_images_actions_keyboard(mat_id)
        )
        await callback.answer()
        return

    if action.startswith("add_image:"):
        mat_id = int(data.split(":")[2])
        await state.update_data(add_image_mat_id=mat_id)
        await state.set_state(AdminStates.waiting_image_upload)
        await callback.message.edit_text(
            "Отправьте фото, которое хотите добавить к материалу.\n"
            "Можно также добавить подпись к фото."
        )
        await callback.answer()
        return

    if action.startswith("delete_mat:"):
        mat_id = int(data.split(":")[2])
        await callback.message.edit_text(
            "⚠️ Вы уверены, что хотите удалить этот материал?",
            reply_markup=admin_confirm_delete_keyboard("mat", mat_id)
        )
        await callback.answer()
        return

    # ---- Подтверждение удаления ----
    if action == "confirm_del":
        del_type = data.split(":")[2]
        item_id = int(data.split(":")[3])

        async with async_session_factory() as session:
            if del_type == "cat":
                await session.execute(
                    delete(Category).where(Category.id == item_id)
                )
                await session.commit()
                msg = "✅ Раздел удалён!"
            elif del_type == "mat":
                await session.execute(
                    delete(Material).where(Material.id == item_id)
                )
                await session.commit()
                msg = "✅ Материал удалён!"
            else:
                msg = "❌ Неизвестный тип удаления."

        await callback.message.edit_text(msg)
        await callback.answer()
        return

    if action == "cancel_del":
        await callback.message.edit_text(
            "❌ Удаление отменено.",
            reply_markup=admin_main_keyboard()
        )
        await callback.answer()
        return

    # ---- Статистика ----
    if action == "stats":
        await callback.message.edit_text(
            "📊 Статистика\n\n"
            "Используйте команду /stats для просмотра статистики.",
            reply_markup=admin_main_keyboard()
        )
        await callback.answer()
        return

    # ---- Управление админами ----
    if action == "admins":
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.is_admin == True)
            )
            admins = result.scalars().all()

        admin_ids = [a.telegram_id for a in admins]
        text = "👑 Текущие администраторы:\n"
        for aid in admin_ids:
            text += f"• {aid}\n"

        await callback.message.edit_text(
            text,
            reply_markup=admin_admins_keyboard(admin_ids)
        )
        await callback.answer()
        return

    if action == "add_admin":
        await state.set_state(AdminStates.waiting_admin_id)
        await callback.message.edit_text(
            "Введите Telegram ID пользователя, которого хотите сделать админом:"
        )
        await callback.answer()
        return

    if action.startswith("remove_admin:"):
        admin_tg_id = int(data.split(":")[2])
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == admin_tg_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.is_admin = False
                await session.commit()
                await callback.message.edit_text(
                    f"✅ Пользователь {admin_tg_id} больше не админ."
                )
            else:
                await callback.message.edit_text(
                    f"❌ Пользователь {admin_tg_id} не найден в базе."
                )
        await callback.answer()
        return

    await callback.answer()


# ---- FSM: Создание раздела ----

@router.message(StateFilter(AdminStates.waiting_category_title))
async def process_category_title(message: Message, state: FSMContext) -> None:
    """Создание нового раздела."""
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте снова:")
        return

    async with async_session_factory() as session:
        # Определяем следующую позицию
        result = await session.execute(
            select(Category).order_by(Category.position.desc()).limit(1)
        )
        last_cat = result.scalar_one_or_none()
        next_pos = (last_cat.position + 1) if last_cat else 0

        category = Category(title=title, position=next_pos)
        session.add(category)
        await session.commit()

    await state.clear()
    await message.answer(
        f"✅ Раздел «{title}» создан!",
        reply_markup=admin_main_keyboard()
    )


# ---- FSM: Переименование раздела ----

@router.message(StateFilter(AdminStates.waiting_category_rename))
async def process_category_rename(message: Message, state: FSMContext) -> None:
    """Переименование раздела."""
    new_title = message.text.strip()
    if not new_title:
        await message.answer("Название не может быть пустым. Попробуйте снова:")
        return

    data = await state.get_data()
    cat_id = data.get("edit_cat_id")

    async with async_session_factory() as session:
        result = await session.execute(
            select(Category).where(Category.id == cat_id)
        )
        cat = result.scalar_one_or_none()
        if cat:
            cat.title = new_title
            await session.commit()
            await message.answer(
                f"✅ Раздел переименован в «{new_title}»!",
                reply_markup=admin_main_keyboard()
            )
        else:
            await message.answer("❌ Раздел не найден.")

    await state.clear()


# ---- FSM: Создание материала ----

@router.callback_query(StateFilter(AdminStates.waiting_material_category))
async def process_material_category_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор категории для нового материала."""
    if not callback.data.startswith("admin:choose_cat_mat:"):
        await callback.answer()
        return

    cat_id = int(callback.data.split(":")[2])
    await state.update_data(new_mat_cat_id=cat_id)
    await state.set_state(AdminStates.waiting_material_title)

    await callback.message.edit_text(
        "Введите название материала:"
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.waiting_material_title))
async def process_material_title(message: Message, state: FSMContext) -> None:
    """Ввод названия материала."""
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(new_mat_title=title)
    await state.set_state(AdminStates.waiting_material_content)
    await message.answer(
        f"Введите текст материала для «{title}»:"
    )


@router.message(StateFilter(AdminStates.waiting_material_content))
async def process_material_content(message: Message, state: FSMContext) -> None:
    """Ввод содержимого материала."""
    content = message.text.strip()
    if not content:
        await message.answer("Содержание не может быть пустым. Попробуйте снова:")
        return

    data = await state.get_data()
    cat_id = data.get("new_mat_cat_id")
    title = data.get("new_mat_title")

    async with async_session_factory() as session:
        # Определяем следующую позицию
        result = await session.execute(
            select(Material)
            .where(Material.category_id == cat_id)
            .order_by(Material.position.desc())
            .limit(1)
        )
        last_mat = result.scalar_one_or_none()
        next_pos = (last_mat.position + 1) if last_mat else 0

        material = Material(
            category_id=cat_id,
            title=title,
            content=content,
            position=next_pos,
        )
        session.add(material)
        await session.commit()

    await state.clear()
    await message.answer(
        f"✅ Материал «{title}» создан!",
        reply_markup=admin_main_keyboard()
    )


# ---- FSM: Редактирование текста материала ----

@router.message(StateFilter(AdminStates.waiting_material_edit_text))
async def process_material_edit_text(message: Message, state: FSMContext) -> None:
    """Редактирование текста материала."""
    new_content = message.text.strip()
    if not new_content:
        await message.answer("Содержание не может быть пустым. Попробуйте снова:")
        return

    data = await state.get_data()
    mat_id = data.get("edit_mat_id")

    async with async_session_factory() as session:
        result = await session.execute(
            select(Material).where(Material.id == mat_id)
        )
        mat = result.scalar_one_or_none()
        if mat:
            mat.content = new_content
            await session.commit()
            await message.answer(
                f"✅ Текст материала «{mat.title}» обновлён!",
                reply_markup=admin_main_keyboard()
            )
        else:
            await message.answer("❌ Материал не найден.")

    await state.clear()


# ---- FSM: Загрузка изображений ----

@router.message(StateFilter(AdminStates.waiting_image_upload), F.photo)
async def process_image_upload(message: Message, state: FSMContext) -> None:
    """Загрузка изображения для материала."""
    data = await state.get_data()
    mat_id = data.get("add_image_mat_id")

    # Берём самое качественное фото (последнее в массиве)
    photo = message.photo[-1]
    file_id = photo.file_id
    caption = message.caption or ""

    async with async_session_factory() as session:
        # Определяем следующую позицию
        result = await session.execute(
            select(Image)
            .where(Image.material_id == mat_id)
            .order_by(Image.position.desc())
            .limit(1)
        )
        last_img = result.scalar_one_or_none()
        next_pos = (last_img.position + 1) if last_img else 0

        image = Image(
            material_id=mat_id,
            file_id=file_id,
            caption=caption,
            position=next_pos,
        )
        session.add(image)
        await session.commit()

    await message.answer(
        "✅ Изображение добавлено!\n\n"
        "Можете отправить ещё фото или нажмите /cancel для выхода.",
        reply_markup=admin_images_actions_keyboard(mat_id)
    )


@router.message(StateFilter(AdminStates.waiting_image_upload), ~F.photo)
async def process_image_upload_invalid(message: Message) -> None:
    """Если прислали не фото."""
    await message.answer(
        "Пожалуйста, отправьте фото. Или нажмите /cancel для отмены."
    )


# ---- FSM: Добавление админа ----

@router.message(StateFilter(AdminStates.waiting_admin_id))
async def process_add_admin(message: Message, state: FSMContext) -> None:
    """Добавление нового админа."""
    try:
        tg_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите число (Telegram ID):")
        return

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == tg_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.is_admin = True
            await session.commit()
            await message.answer(
                f"✅ Пользователь {tg_id} теперь администратор!",
                reply_markup=admin_main_keyboard()
            )
        else:
            # Создаём пользователя с правами админа
            new_user = User(telegram_id=tg_id, is_admin=True)
            session.add(new_user)
            await session.commit()
            await message.answer(
                f"✅ Пользователь {tg_id} добавлен в базу и назначен администратором!\n"
                f"Он получит права после того, как напишет боту /start.",
                reply_markup=admin_main_keyboard()
            )

    await state.clear()


# ---- Отмена FSM ----

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Отмена текущего действия."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного действия для отмены.")
        return

    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=admin_main_keyboard()
    )
