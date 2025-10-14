import asyncio
import traceback
import typing

from app.store.game import BotResponse, Game

from .accessor import BotAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application

    from .dataclasses import UpdateObj


class BotManager:
    """Менеджер для обработки обновлений телеграм-бота."""
    
    def __init__(self, app: "Application", queue: asyncio.Queue):
        """Инициализация менеджера бота."""
        self.bot_accessor = BotAccessor(app.config.bot.token)
        self.queue = queue
        self.max_threads = app.config.bot.max_threads
        self._tasks: list[asyncio.Task] = []
        self.game = Game(app)

    async def process_update(self, update: "UpdateObj") -> None:
        """Обработка входящего обновления."""
        response = await self.game.handle(update)
        
        if response.status == "redirect":
            await self.send_response(response)
            response = await self.game.delay_handler(response)
            await self.send_response(response)
            response = await self.game.delay_handler(response)
        
        await self.send_response(response)

    async def send_response(self, response: BotResponse) -> None:
        """Отправка ответа пользователю."""
        if response.status == "pass":
            return
        
        try:
            await self.bot_accessor.send_message(
                response.chat_id, 
                response.message, 
                response.reply_markup
            )
        except Exception:
            pass

    async def _worker_loop(self) -> None:
        """Основной цикл обработки обновлений."""
        while True:
            update = await self.queue.get()
            try:
                await self.process_update(update)
            except Exception:
                traceback.print_exc()
            finally:
                self.queue.task_done()

    async def start_processing(self) -> None:
        """Запуск обработки обновлений."""
        self._tasks = [
            asyncio.create_task(self._worker_loop()) 
            for _ in range(self.max_threads)
        ]

    async def stop_processing(self) -> None:
        """Остановка обработки обновлений."""
        await self.queue.join()
        for task in self._tasks:
            task.cancel()
