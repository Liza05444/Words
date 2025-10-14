import typing
from dataclasses import dataclass
from pathlib import Path

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    """Конфигурация сессий."""
    key: str


@dataclass
class AdminConfig:
    """Конфигурация администратора."""
    email: str
    password: str


@dataclass
class BotConfig:
    """Конфигурация телеграм-бота."""
    token: str
    id: int
    max_threads: int


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных."""
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class WebConfig:
    """Конфигурация веб-сервера."""
    host: str
    port: int


@dataclass
class Config:
    """Основная конфигурация приложения."""
    admin: AdminConfig
    session: SessionConfig | None = None
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None
    web: WebConfig | None = None


def load_configuration(config_path: str) -> dict:
    """Загрузка конфигурации из YAML файла."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")
    
    with config_file.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def setup_config(app: "Application", config_path: str) -> None:
    """Настройка конфигурации приложения."""
    raw_config = load_configuration(config_path)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            id=raw_config["bot"]["id"],
            max_threads=raw_config["bot"]["max_threads"],
        ),
        database=DatabaseConfig(**raw_config["database"]) if raw_config.get("database") else None,
        web=WebConfig(
            host=raw_config["web"]["host"],
            port=raw_config["web"]["port"],
        ),
    )
