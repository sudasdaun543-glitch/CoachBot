from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from web.config import SECRET_KEY
from web.routes import admin, public
from web.template_utils import templates


def get_serializer() -> URLSafeTimedSerializer:
    """Возвращает сериализатор для session cookie."""
    return URLSafeTimedSerializer(SECRET_KEY)


class TemplateContextMiddleware(BaseHTTPMiddleware):
    """Middleware, добавляющий данные пользователя в request.state."""

    async def dispatch(self, request: Request, call_next):
        # SessionMiddleware уже обработал запрос к этому моменту,
        # так как BaseHTTPMiddleware добавляется после SessionMiddleware
        session = request.scope.get("session", {})
        request.state.user = session.get("user")
        request.state.is_admin = session.get("is_admin", False)
        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    # При старте ничего не делаем (БД инициализируется при первом запросе)
    yield


app = FastAPI(title="Coaching Operators", lifespan=lifespan)

# Подключаем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Контекст-процессор для шаблонов (добавляем ПОСЛЕ SessionMiddleware)
app.add_middleware(TemplateContextMiddleware)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Подключаем роутеры
app.include_router(public.router)
app.include_router(admin.router)
