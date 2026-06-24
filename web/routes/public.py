from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from bot.database import async_session_factory
from bot.models import Category, Image, Material
from web.auth import verify_telegram_login
from web.config import ADMIN_IDS, TELEGRAM_BOT_NAME
from web.template_utils import get_templates

router = APIRouter()
templates = get_templates()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница со списком разделов."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Category).order_by(Category.position)
        )
        categories = result.scalars().all()

    return templates.TemplateResponse(
        "public/index.html",
        {"request": request, "categories": categories},
    )


@router.get("/category/{category_id}", response_class=HTMLResponse)
async def category_page(request: Request, category_id: int):
    """Страница раздела со списком материалов."""
    async with async_session_factory() as session:
        cat_result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = cat_result.scalar_one_or_none()

        if not category:
            return templates.TemplateResponse(
                "public/index.html",
                {"request": request, "error": "Раздел не найден"},
                status_code=404,
            )

        mat_result = await session.execute(
            select(Material)
            .where(Material.category_id == category_id)
            .order_by(Material.position)
        )
        materials = mat_result.scalars().all()

    return templates.TemplateResponse(
        "public/category.html",
        {
            "request": request,
            "category": category,
            "materials": materials,
        },
    )


@router.get("/material/{material_id}", response_class=HTMLResponse)
async def material_page(request: Request, material_id: int):
    """Страница материала с текстом и изображениями."""
    from web.config import TELEGRAM_BOT_TOKEN

    async with async_session_factory() as session:
        mat_result = await session.execute(
            select(Material).where(Material.id == material_id)
        )
        material = mat_result.scalar_one_or_none()

        if not material:
            return templates.TemplateResponse(
                "public/index.html",
                {"request": request, "error": "Материал не найден"},
                status_code=404,
            )

        img_result = await session.execute(
            select(Image)
            .where(Image.material_id == material_id)
            .order_by(Image.position)
        )
        images = img_result.scalars().all()

    return templates.TemplateResponse(
        "public/material.html",
        {
            "request": request,
            "material": material,
            "images": images,
            "telegram_bot_token": TELEGRAM_BOT_TOKEN,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа через Telegram."""
    return templates.TemplateResponse(
        "public/login.html",
        {
            "request": request,
            "bot_name": TELEGRAM_BOT_NAME,
        },
    )


@router.post("/auth/telegram")
async def auth_telegram(request: Request):
    """Обработка Telegram Login Widget."""
    form = await request.form()
    data = dict(form)

    if not verify_telegram_login(data):
        return templates.TemplateResponse(
            "public/login.html",
            {
                "request": request,
                "error": "Ошибка авторизации. Попробуйте снова.",
                "bot_name": TELEGRAM_BOT_NAME,
            },
            status_code=400,
        )

    tg_id = int(data.get("id", 0))
    username = data.get("username", "")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    # Сохраняем в сессию
    request.session["user"] = {
        "id": tg_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    }
    request.session["is_admin"] = tg_id in ADMIN_IDS

    # Регистрируем/обновляем пользователя в БД
    from sqlalchemy import select as sql_select

    from bot.models import User

    async with async_session_factory() as session:
        result = await session.execute(
            sql_select(User).where(User.telegram_id == tg_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            if tg_id in ADMIN_IDS:
                user.is_admin = True
        else:
            user = User(
                telegram_id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=tg_id in ADMIN_IDS,
            )
            session.add(user)
        await session.commit()

    # Если админ — редирект в админку, иначе на главную
    if tg_id in ADMIN_IDS:
        return RedirectResponse(url="/admin", status_code=302)
    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    """Выход из системы."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
