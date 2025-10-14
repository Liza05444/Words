from aiohttp.web_app import Application

__all__ = ("configure_routes",)


def configure_routes(app: Application) -> None:
    """Настройка всех маршрутов приложения."""
    from app.admin.routes import configure_admin_routes
    from app.users.routes import configure_user_routes

    configure_user_routes(app)
    configure_admin_routes(app)
