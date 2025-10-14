import base64

from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import get_session, new_session

from app.admin.schema import AdminInSchema, SessionListSchema, UserListSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response


class AdminLoginView(View):
    @docs(
        tags=["Admin"], 
        summary="Авторизация администратора", 
        description="Вход в систему администратора по telegram_id"
    )
    @request_schema(AdminInSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        auth = await AuthRequiredMixin.set_auth(role="admin", data=self.data, acc=self.store.user_accessor)
        session = await new_session(request=self.request)
        session["auth"] = auth
        return json_response(data={"auth": auth})


class AdminCurrentView(View):
    @docs(
        tags=["Admin"], 
        summary="Текущий администратор", 
        description="Получение информации о текущем авторизованном администраторе"
    )
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        s = await get_session(self.request)
        admin = await AuthRequiredMixin.get_auth(role="admin", user=s["auth"], acc=self.store.user_accessor)
        return json_response(data={"user": admin.id, "session": admin.name})


class AdminChatView(View):
    @docs(
        tags=["Admin"], 
        summary="Список чатов", 
        description="Получение списка игровых сессий, где пользователь является администратором"
    )
    @response_schema(SessionListSchema, 200)
    async def get(self):
        s = await get_session(self.request)
        admin = int(base64.b64decode(s["auth"].encode()).decode().split()[1])
        data = await self.store.session_accessor.find_session_by_admin(admin)
        return json_response(data=SessionListSchema().dump({"amount": len(data), "sessions": data}))


class AdminUserView(View):
    @docs(
        tags=["Admin"], 
        summary="Пользователи сессий", 
        description="Получение списка пользователей и результатов игровых сессий"
    )
    @response_schema(UserListSchema, 200)
    async def get(self):
        s = await get_session(self.request)
        admin = int(base64.b64decode(s["auth"].encode()).decode().split()[1])
        ses = await self.store.session_accessor.find_session_by_admin(admin)
        sessions = []
        for el in ses:
            users = await self.store.user_accessor.get_users(el.id)
            sessions.append({"amount": len(users), "users": users})
        data = {"amount": len(ses), "sessions": sessions}
        return json_response(data=UserListSchema().dump(data))
