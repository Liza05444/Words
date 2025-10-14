import asyncio
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application

from .manager import BotManager
from .poller import Poller


class Bot:
    def __init__(self, app: "Application"):
        self.queue = asyncio.Queue()
        self.poller = Poller(app.config.bot.token, self.queue)
        self.manager = BotManager(app, self.queue)

        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    async def connect(self, app: "Application"):
        if app.database and app.database.session is None:
            await app.database.connect()
        
        await self.poller.start()
        await self.manager.start_processing()

    async def disconnect(self, app: "Application"):
        await self.poller.stop()
        await self.manager.stop_processing()
