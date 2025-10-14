from aiohttp.web_app import Application

__all__ = ("configure_user_routes",)


def configure_user_routes(app: Application) -> None:
    """Настройка маршрутов для пользовательских API."""
    from app.users.views import UserChatView, UserCurrentView, UserLoginView, UserStatView

    app.router.add_view("/user.login", UserLoginView)
    app.router.add_view("/user.current", UserCurrentView)
    app.router.add_view("/user.chats", UserChatView)
    app.router.add_view("/user.results", UserStatView)
