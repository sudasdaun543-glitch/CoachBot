from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ADMIN_IDS
from bot.database import async_session_factory
from bot.models import Category, Material, UsageStats, User

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Показывает статистику бота (только для админов)."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к статистике.")
        return

    async with async_session_factory() as session:
        # Общее количество пользователей
        total_users_result = await session.execute(
            select(func.count(User.id))
        )
        total_users = total_users_result.scalar()

        # Количество админов
        admins_result = await session.execute(
            select(func.count(User.id)).where(User.is_admin == True)
        )
        total_admins = admins_result.scalar()

        # Общее количество просмотров
        total_views_result = await session.execute(
            select(func.count(UsageStats.id))
        )
        total_views = total_views_result.scalar()

        # Количество разделов
        cats_result = await session.execute(
            select(func.count(Category.id))
        )
        total_cats = cats_result.scalar()

        # Количество материалов
        mats_result = await session.execute(
            select(func.count(Material.id))
        )
        total_mats = mats_result.scalar()

        # Просмотры по разделам (через материалы)
        stats_text = ""
        cats = await session.execute(
            select(Category).order_by(Category.position)
        )
        for cat in cats.scalars().all():
            # Получаем ID материалов в этой категории
            mat_ids_result = await session.execute(
                select(Material.id).where(Material.category_id == cat.id)
            )
            mat_ids = [row[0] for row in mat_ids_result.all()]

            if mat_ids:
                views_result = await session.execute(
                    select(func.count(UsageStats.id))
                    .where(
                        UsageStats.material_id.in_(mat_ids),
                        UsageStats.action == "view_material",
                    )
                )
                cat_views = views_result.scalar()
            else:
                cat_views = 0

            stats_text += f"📁 {cat.title}: {cat_views} просмотров\n"

    text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"👑 Администраторов: {total_admins}\n"
        f"📂 Разделов: {total_cats}\n"
        f"📄 Материалов: {total_mats}\n"
        f"👁 Всего просмотров: {total_views}\n\n"
        f"**По разделам:**\n{stats_text}"
    )

    await message.answer(text)
