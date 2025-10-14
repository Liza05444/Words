import ssl

import aiohttp

from .dataclasses import GetUpdatesResponse, SendMessageResponse


class BotAccessor:
    def __init__(self, token: str = ""):
        self.token = token
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self._connector = None
        self._session = None
    
    @property
    def connector(self):
        if self._connector is None:
            self._connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        return self._connector
    
    @property
    def session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(connector=self.connector)
        return self._session

    def get_url(self, method: str):
        return f"https://api.telegram.org/bot{self.token}/{method}"

    async def get_updates(self, offset: int | None = None, poll_timeout: int = 0) -> dict:
        url = self.get_url("getUpdates")
        params = {}
        if offset:
            params["offset"] = offset
        if poll_timeout:
            params["timeout"] = poll_timeout
        try:
            async with self.session.get(url, params=params) as resp:
                return await resp.json()
        except Exception as e:
            if "Session is closed" in str(e):
                self._session = None
            return {"ok": False, "result": []}

    async def get_updates_in_objects(self, offset: int | None = None, poll_timeout: int = 0) -> GetUpdatesResponse:
        try:
            res_dict = await self.get_updates(offset=offset, poll_timeout=poll_timeout)
            return GetUpdatesResponse.load(res_dict)
        except Exception:
            return GetUpdatesResponse(ok=False, result=[])

    async def send_message(self, chat_id: int, text: str, reply_markup: dict) -> SendMessageResponse:
        url = self.get_url("sendMessage")
        payload = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
        try:
            async with self.session.post(url, json=payload) as resp:
                res_dict = await resp.json()
                try:
                    return SendMessageResponse.load(res_dict)
                except KeyError:
                    res_dict["result"] = None
                    return SendMessageResponse.load(res_dict)
        except Exception as e:
            if "Session is closed" in str(e):
                self._session = None
            return SendMessageResponse.load({"ok": False, "result": None})
