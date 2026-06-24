from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.models import Category, Material


def main_menu_keyboard(
    categories: list[Category], web_app_url: str = ""
) -> InlineKeyboardMarkup:
    """Главное меню со списком разделов."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.title, callback_data=f"category:{cat.id}")
    if web_app_url:
        builder.button(
            text="🌐 Открыть веб-версию",
            url=web_app_url,
        )
    builder.adjust(1)
    return builder.as_markup()


def materials_keyboard(
    materials: list[Material], category_id: int
) -> InlineKeyboardMarkup:
    """Список материалов в разделе."""
    builder = InlineKeyboardBuilder()
    for mat in materials:
        builder.button(text=mat.title, callback_data=f"material:{mat.id}")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def material_navigation_keyboard(
    material_id: int, category_id: int
) -> InlineKeyboardMarkup:
    """Кнопки навигации после просмотра материала."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К списку", callback_data=f"category:{category_id}")
    builder.button(text="🏠 Главное меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
