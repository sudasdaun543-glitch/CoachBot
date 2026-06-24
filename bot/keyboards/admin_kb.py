from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.models import Category, Material


def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📂 Управление разделами", callback_data="admin:categories")
    builder.button(text="📄 Управление материалами", callback_data="admin:materials")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.button(text="👑 Управление админами", callback_data="admin:admins")
    builder.button(text="🔙 Выйти", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_categories_list_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    """Список разделов для админа."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.title} (ред.)", callback_data=f"admin:edit_cat:{cat.id}"
        )
    builder.button(text="➕ Создать раздел", callback_data="admin:create_cat")
    builder.button(text="🔙 Назад", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Действия с разделом."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"admin:rename_cat:{category_id}")
    builder.button(text="❌ Удалить", callback_data=f"admin:delete_cat:{category_id}")
    builder.button(text="🔙 Назад", callback_data="admin:categories")
    builder.adjust(1)
    return builder.as_markup()


def admin_materials_list_keyboard(materials: list[Material]) -> InlineKeyboardMarkup:
    """Список материалов для админа (с выбором категории)."""
    builder = InlineKeyboardBuilder()
    for mat in materials:
        builder.button(
            text=f"{mat.title} (ред.)", callback_data=f"admin:edit_mat:{mat.id}"
        )
    builder.button(text="➕ Создать материал", callback_data="admin:create_mat")
    builder.button(text="🔙 Назад", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_material_actions_keyboard(material_id: int) -> InlineKeyboardMarkup:
    """Действия с материалом."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать текст", callback_data=f"admin:edit_mat_text:{material_id}")
    builder.button(text="🖼 Управление фото", callback_data=f"admin:edit_mat_images:{material_id}")
    builder.button(text="❌ Удалить", callback_data=f"admin:delete_mat:{material_id}")
    builder.button(text="🔙 Назад", callback_data="admin:materials")
    builder.adjust(1)
    return builder.as_markup()


def admin_images_actions_keyboard(material_id: int) -> InlineKeyboardMarkup:
    """Действия с изображениями материала."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить фото", callback_data=f"admin:add_image:{material_id}")
    builder.button(text="🔙 Назад", callback_data=f"admin:edit_mat:{material_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_confirm_delete_keyboard(
    action: str, item_id: int
) -> InlineKeyboardMarkup:
    """Подтверждение удаления."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin:confirm_del:{action}:{item_id}")
    builder.button(text="❌ Отмена", callback_data=f"admin:cancel_del")
    builder.adjust(1)
    return builder.as_markup()


def admin_category_choice_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    """Выбор категории для создания материала."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.title, callback_data=f"admin:choose_cat_mat:{cat.id}")
    builder.button(text="🔙 Назад", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def admin_admins_keyboard(admin_ids: list[int]) -> InlineKeyboardMarkup:
    """Управление админами."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить админа", callback_data="admin:add_admin")
    for aid in admin_ids:
        builder.button(text=f"❌ Удалить {aid}", callback_data=f"admin:remove_admin:{aid}")
    builder.button(text="🔙 Назад", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()
