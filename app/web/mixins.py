import base64

from aiohttp.web_exceptions import HTTPForbidden

from app.store.accessors.user_accessor import UserAccessor
from app.users.models import PlayerModel


class AuthRequiredMixin:
    permissions = {"admin": ["user", "admin"], "user": ["user"]}

    @staticmethod
    async def set_auth(role: str, data: dict[str, str], acc: UserAccessor) -> str:
        auth = None
        if role == "admin":
            auth = await acc.find_admin_by_tg(int(data["telegram_id"]))
        elif role == "user":
            auth = await acc.find_user_by_tg(int(data["telegram_id"]))
        if auth is None:
            raise HTTPForbidden
        s = f"{role} {auth.telegram_id}"
        return base64.b64encode(s.encode()).decode()

    @staticmethod
    async def get_auth(role: str, user: str, acc: UserAccessor) -> PlayerModel | None:
        credentials = base64.b64decode(user.encode()).decode().split()
        if role not in AuthRequiredMixin.permissions.get(credentials[0], []):
            return None
        auth = None
        if role == "admin":
            auth = await acc.find_admin_by_tg(int(credentials[1]))
        elif role == "user":
            auth = await acc.find_user_by_tg(int(credentials[1]))
        return auth
