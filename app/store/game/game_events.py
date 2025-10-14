import typing

if typing.TYPE_CHECKING:
    from app.store.bot.dataclasses import Message
    from app.web.app import Application


class GameEvents:
    def __init__(self, app: "Application"):
        self.app = app
        self.events = {
            "new": self.new_member,
            "old": self.old_member,
            "new_bot": self.add_bot,
            "old_bot": self.del_bot,
        }

    async def event(self, message: "Message"):
        com = message.data.split()
        if com[1] == str(self.app.config.bot.id):
            com = [com[0] + "_bot", message.from_.id, message.from_.first_name + " " + (message.from_.last_name or "")]
        await self.events[com[0]](message.chat.id, message.chat.title, *com[1:])

    async def add_bot(self, chat_id: int, chat_name: str, *args):
        session = await self.app.store.session_accessor.add_session(chat_id, chat_name)
        user = await self.app.store.user_accessor.find_user_by_tg(args[0])
        if user is None:
            user = await self.app.store.user_accessor.add_user(args[0], args[1])
        await self.app.store.user_accessor.add_usersession(session.id, user.id)
        await self.app.store.user_accessor.add_admin(user.id, session.id)

    async def del_bot(self, chat_id: int, chat_name: str, *args):
        await self.app.store.session_accessor.del_session(chat_id)

    async def new_member(self, chat_id: int, chat_name: str, *args):
        user = await self.app.store.user_accessor.find_user_by_tg(int(args[0]))
        if user is None:
            user = await self.app.store.user_accessor.add_user(int(args[0]), args[1] + " " + args[2])
        session = await self.app.store.session_accessor.find_session_by_group(chat_id)
        if await self.app.store.user_accessor.find_usersession(session.id, user.id) is None:
            await self.app.store.user_accessor.add_usersession(session.id, user.id)
            await self.app.store.session_accessor.set_member_amount(chat_id, 1)
        return user

    async def old_member(self, chat_id: int, chat_name: str, *args):
        await self.app.store.user_accessor.del_usersession(chat_id, int(args[0]))
        await self.app.store.session_accessor.set_member_amount(chat_id, -1)
