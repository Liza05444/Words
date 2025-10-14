
from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.store.database.database import Database
from app.store.store import Store, setup_store
from app.web.config import Config, setup_config
from app.web.mw import configure_middlewares
from app.web.routes import configure_routes

__all__ = ("Application", "Request", "View")


class Application(AiohttpApplication):
    """Расширенное приложение с дополнительными атрибутами."""
    config: Config | None = None
    store: Store | None = None
    database: Database | None = None


class Request(AiohttpRequest):
    """Кастомный запрос с типизированным приложением."""
    
    @property
    def app(self) -> Application:
        """Получение экземпляра приложения."""
        return super().app()


class View(AiohttpView):
    """Базовый класс для представлений с удобными свойствами."""
    
    @property
    def request(self) -> Request:
        """Получение текущего запроса."""
        return super().request

    @property
    def database(self) -> Database:
        """Получение подключения к базе данных."""
        return self.request.app.database

    @property
    def store(self) -> Store:
        """Получение хранилища данных."""
        return self.request.app.store

    @property
    def data(self) -> dict:
        """Получение данных запроса."""
        return self.request.get("data", {})


def create_application() -> Application:
    """Создание нового экземпляра приложения."""
    return Application()


def setup_app(config_path: str) -> Application:
    """Настройка и инициализация приложения."""
    app = create_application()
    setup_config(app, config_path)
    session_setup(app, EncryptedCookieStorage(app.config.session.key))
    configure_routes(app)
    setup_aiohttp_apispec(
        app, 
        title="Telegram Word Game Bot API", 
        version="1.0.0",
        url="/docs/json", 
        swagger_path="/docs",
        info={
            "description": "API для управления игрой в слова через Telegram бота",
            "contact": {
                "name": "Admin API Support"
            }
        },
        servers=[
            {
                "url": f"http://{app.config.web.host}:{app.config.web.port}",
                "description": "Development server"
            }
        ]
    )
    configure_middlewares(app)
    setup_store(app)
    return app
