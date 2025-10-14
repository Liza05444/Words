import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    """Центральное хранилище данных и сервисов приложения."""
    
    def __init__(self, app: "Application", *args, **kwargs):
        """Инициализация хранилища с подключением всех сервисов."""
        from app.store.accessors.round_accessor import RoundAccessor
        from app.store.accessors.session_accessor import SessionAccessor
        from app.store.accessors.user_accessor import UserAccessor
        from app.store.bot import Bot
        from app.store.game import Game

        self.user_accessor = UserAccessor(app)
        self.session_accessor = SessionAccessor(app)
        self.round_accessor = RoundAccessor(app)
        self.bot = Bot(app)
        self.game = Game(app)


def initialize_database(app: "Application") -> Database:
    """Инициализация подключения к базе данных."""
    database = Database(app)
    app.on_startup.append(database.connect)
    app.on_cleanup.append(database.disconnect)
    return database


def setup_store(app: "Application") -> None:
    """Настройка хранилища данных для приложения."""
    app.database = initialize_database(app)
    app.store = Store(app)
