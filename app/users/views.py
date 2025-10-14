import base64

from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import get_session, new_session

from app.users.schema import ChatListSchema, ResultListSchema, UserInSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response


class UserLoginView(View):
    @docs(tags=["User"], summary="Sign in as user", description="Sign in as user")
    @request_schema(UserInSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        auth = await AuthRequiredMixin.set_auth(role="user", data=self.data, acc=self.store.user_accessor)
        session = await new_session(request=self.request)
        session["auth"] = auth
        return json_response(data={"auth": auth})


class UserCurrentView(View):
    @docs(tags=["User"], summary="Check user", description="Check user account")
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        s = await get_session(self.request)
        auth = await AuthRequiredMixin.get_auth(role="user", user=s["auth"], acc=self.store.user_accessor)
        return json_response(data={"user": auth.telegram_id, "session": auth.name})


class UserChatView(View):
    @docs(tags=["User"], summary="Get chats", description="Get chats where user is")
    @response_schema(ChatListSchema, 200)
    async def get(self):
        s = await get_session(self.request)
        user = int(base64.b64decode(s["auth"].encode()).decode().split()[1])
        data = await self.store.session_accessor.find_session_by_user_tg(user)
        return json_response(data=ChatListSchema().dump({"sessions": data}))


class UserStatView(View):
    @docs(tags=["User"], summary="Get results", description="Get results of sessions")
    @response_schema(ResultListSchema, 200)
    async def get(self):
        s = await get_session(self.request)
        user = int(base64.b64decode(s["auth"].encode()).decode().split()[1])
        ses = await self.store.session_accessor.find_session_by_user_tg(user)
        res = [await self.store.session_accessor.get_result(el.id) for el in ses]
        data = {
            "results": [
                {"chat": ses[i].chat_name, "result": [{"name": name, "count": count} for name, count in res[i].items()]}
                for i in range(len(res))
            ]
        }
        return json_response(data=ResultListSchema().dump(data))
