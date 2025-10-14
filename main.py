from pathlib import Path

from aiohttp.web import run_app

from app.web.app import setup_app


def main():
    """Инициализация и запуск веб-приложения."""
    config_file = Path(__file__).parent / "etc" / "config.yaml"
    application = setup_app(str(config_file))
    
    # Получаем конфигурацию для веб-сервера
    web_config = application.config.web
    host = web_config.host if web_config else "127.0.0.1"
    port = web_config.port if web_config else 8001
    
    run_app(application, host=host, port=port)


if __name__ == "__main__":
    main()
