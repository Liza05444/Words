import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def configure_admin_routes(app: "Application") -> None:
    """Настройка маршрутов для административных API."""
    from app.admin.views import AdminChatView, AdminCurrentView, AdminLoginView, AdminUserView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.chats", AdminChatView)
    app.router.add_view("/admin.users", AdminUserView)
