from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="web/templates")


def get_templates() -> Jinja2Templates:
    """Возвращает экземпляр Jinja2Templates."""
    return templates
