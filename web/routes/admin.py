from functools import wraps

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import delete, select

from bot.database import async_session_factory
from bot.models import Category, Image, Material, UsageStats, User
from web.template_utils import get_templates

router = APIRouter()
templates = get_templates()


def admin_required(func):
    """Декоратор для проверки прав админа."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Используем request.state.is_admin из TemplateContextMiddleware
        if not request.state.is_admin:
            return templates.TemplateResponse(
                "public/login.html",
                {
                    "request": request,
                    "error": "Требуется авторизация администратора",
                    "bot_name": "",
                },
                status_code=403,
            )
        return await func(request, *args, **kwargs)
    return wrapper


@router.get("/admin", response_class=HTMLResponse)
@admin_required
async def admin_dashboard(request: Request):
    """Админ-дашборд."""
    async with async_session_factory() as session:
        # Статистика
        from sqlalchemy import func

        total_users = (await session.execute(select(func.count(User.id)))).scalar()
        total_cats = (await session.execute(select(func.count(Category.id)))).scalar()
        total_mats = (await session.execute(select(func.count(Material.id)))).scalar()
        total_views = (await session.execute(select(func.count(UsageStats.id)))).scalar()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "total_users": total_users,
            "total_cats": total_cats,
            "total_mats": total_mats,
            "total_views": total_views,
        },
    )


# ==================== КАТЕГОРИИ ====================


@router.get("/admin/categories", response_class=HTMLResponse)
@admin_required
async def admin_categories(request: Request):
    """Список разделов."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Category).order_by(Category.position)
        )
        categories = result.scalars().all()

    return templates.TemplateResponse(
        "admin/categories.html",
        {"request": request, "categories": categories},
    )


@router.post("/admin/categories/create")
@admin_required
async def admin_category_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
):
    """Создание раздела."""
    async with async_session_factory() as session:
        # Определяем следующую позицию
        result = await session.execute(
            select(Category).order_by(Category.position.desc()).limit(1)
        )
        last = result.scalar_one_or_none()
        next_pos = (last.position + 1) if last else 0

        cat = Category(title=title, description=description, position=next_pos)
        session.add(cat)
        await session.commit()

    return RedirectResponse(url="/admin/categories", status_code=302)


@router.post("/admin/categories/{cat_id}/edit")
@admin_required
async def admin_category_edit(
    request: Request,
    cat_id: int,
    title: str = Form(...),
    description: str = Form(""),
):
    """Редактирование раздела."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Category).where(Category.id == cat_id)
        )
        cat = result.scalar_one_or_none()
        if cat:
            cat.title = title
            cat.description = description
            await session.commit()

    return RedirectResponse(url="/admin/categories", status_code=302)


@router.post("/admin/categories/{cat_id}/delete")
@admin_required
async def admin_category_delete(request: Request, cat_id: int):
    """Удаление раздела."""
    async with async_session_factory() as session:
        await session.execute(
            delete(Category).where(Category.id == cat_id)
        )
        await session.commit()

    return RedirectResponse(url="/admin/categories", status_code=302)


# ==================== МАТЕРИАЛЫ ====================


@router.get("/admin/materials", response_class=HTMLResponse)
@admin_required
async def admin_materials(request: Request):
    """Список материалов (с фильтром по разделу)."""
    async with async_session_factory() as session:
        cats = (await session.execute(
            select(Category).order_by(Category.position)
        )).scalars().all()

        mats = (await session.execute(
            select(Material).order_by(Material.position)
        )).scalars().all()

    return templates.TemplateResponse(
        "admin/materials.html",
        {"request": request, "categories": cats, "materials": mats},
    )


@router.post("/admin/materials/create")
@admin_required
async def admin_material_create(
    request: Request,
    category_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(""),
):
    """Создание материала."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Material)
            .where(Material.category_id == category_id)
            .order_by(Material.position.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        next_pos = (last.position + 1) if last else 0

        mat = Material(
            category_id=category_id,
            title=title,
            content=content,
            position=next_pos,
        )
        session.add(mat)
        await session.commit()

    return RedirectResponse(url="/admin/materials", status_code=302)


@router.post("/admin/materials/{mat_id}/edit")
@admin_required
async def admin_material_edit(
    request: Request,
    mat_id: int,
    title: str = Form(...),
    content: str = Form(""),
):
    """Редактирование материала."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Material).where(Material.id == mat_id)
        )
        mat = result.scalar_one_or_none()
        if mat:
            mat.title = title
            mat.content = content
            await session.commit()

    return RedirectResponse(url="/admin/materials", status_code=302)


@router.post("/admin/materials/{mat_id}/delete")
@admin_required
async def admin_material_delete(request: Request, mat_id: int):
    """Удаление материала."""
    async with async_session_factory() as session:
        await session.execute(
            delete(Material).where(Material.id == mat_id)
        )
        await session.commit()

    return RedirectResponse(url="/admin/materials", status_code=302)


# ==================== ИЗОБРАЖЕНИЯ ====================


@router.get("/admin/materials/{mat_id}/images", response_class=HTMLResponse)
@admin_required
async def admin_material_images(request: Request, mat_id: int):
    """Управление изображениями материала."""
    async with async_session_factory() as session:
        mat = (await session.execute(
            select(Material).where(Material.id == mat_id)
        )).scalar_one_or_none()

        if not mat:
            return RedirectResponse(url="/admin/materials", status_code=302)

        images = (await session.execute(
            select(Image)
            .where(Image.material_id == mat_id)
            .order_by(Image.position)
        )).scalars().all()

    return templates.TemplateResponse(
        "admin/images.html",
        {"request": request, "material": mat, "images": images},
    )


@router.post("/admin/materials/{mat_id}/images/add")
@admin_required
async def admin_image_add(
    request: Request,
    mat_id: int,
    file_id: str = Form(...),
    caption: str = Form(""),
):
    """Добавление изображения (по file_id из Telegram)."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Image)
            .where(Image.material_id == mat_id)
            .order_by(Image.position.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        next_pos = (last.position + 1) if last else 0

        img = Image(
            material_id=mat_id,
            file_id=file_id,
            caption=caption,
            position=next_pos,
        )
        session.add(img)
        await session.commit()

    return RedirectResponse(
        url=f"/admin/materials/{mat_id}/images", status_code=302
    )


@router.post("/admin/images/{img_id}/delete")
@admin_required
async def admin_image_delete(request: Request, img_id: int):
    """Удаление изображения."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Image).where(Image.id == img_id)
        )
        img = result.scalar_one_or_none()
        mat_id = img.material_id if img else 0

        await session.execute(
            delete(Image).where(Image.id == img_id)
        )
        await session.commit()

    return RedirectResponse(
        url=f"/admin/materials/{mat_id}/images", status_code=302
    )


# ==================== СТАТИСТИКА ====================


@router.get("/admin/stats", response_class=HTMLResponse)
@admin_required
async def admin_stats(request: Request):
    """Статистика."""
    async with async_session_factory() as session:
        from sqlalchemy import func

        total_users = (await session.execute(select(func.count(User.id)))).scalar()
        total_admins = (await session.execute(
            select(func.count(User.id)).where(User.is_admin == True)
        )).scalar()
        total_cats = (await session.execute(select(func.count(Category.id)))).scalar()
        total_mats = (await session.execute(select(func.count(Material.id)))).scalar()
        total_views = (await session.execute(select(func.count(UsageStats.id)))).scalar()

        # Статистика по разделам
        cats = (await session.execute(
            select(Category).order_by(Category.position)
        )).scalars().all()

        cat_stats = []
        for cat in cats:
            mat_ids = (await session.execute(
                select(Material.id).where(Material.category_id == cat.id)
            )).scalars().all()

            if mat_ids:
                views = (await session.execute(
                    select(func.count(UsageStats.id))
                    .where(
                        UsageStats.material_id.in_(mat_ids),
                        UsageStats.action == "view_material",
                    )
                )).scalar()
            else:
                views = 0

            cat_stats.append({"title": cat.title, "views": views})

    return templates.TemplateResponse(
        "admin/stats.html",
        {
            "request": request,
            "total_users": total_users,
            "total_admins": total_admins,
            "total_cats": total_cats,
            "total_mats": total_mats,
            "total_views": total_views,
            "cat_stats": cat_stats,
        },
    )
