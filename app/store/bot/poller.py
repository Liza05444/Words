import asyncio
import traceback
from asyncio import Task

from .accessor import BotAccessor


class Poller:
    def __init__(self, token: str, queue: asyncio.Queue):
        self.bot_accessor = BotAccessor(token)
        self.queue = queue
        self._task: Task | None = None

    async def _poll(self):
        offset = 0
        while True:
            try:
                res = await self.bot_accessor.get_updates_in_objects(offset=offset, poll_timeout=60)

                if not res.ok:
                    await asyncio.sleep(5)
                    continue
                
                for u in res.result:
                    offset = u.update_id + 1
                    self.queue.put_nowait(u)
                    
            except KeyError:
                await asyncio.sleep(5)
                continue
            except Exception as e:
                traceback.print_exc()
                
                if "Session is closed" in str(e):
                    self.bot_accessor._connector = None
                    self.bot_accessor._session = None
                elif "Conflict" in str(e) or "409" in str(e):
                    await asyncio.sleep(10)
                    continue
                
                await asyncio.sleep(5)

    async def start(self):
        self._task = asyncio.create_task(self._poll())

    async def stop(self):
        self._task.cancel()
