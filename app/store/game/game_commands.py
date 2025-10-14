import typing
from random import randint

from app.store.game import BotResponse

if typing.TYPE_CHECKING:
    from app.store.bot.dataclasses import Message
    from app.web.app import Application


class GameCommands:
    states = ["off", "add", "step", "vote", "error"]

    def __init__(self, app: "Application"):
        self.app = app
        self.commands = {
            "/start": self.com_start,
            "/help": self.com_help,
            "/deadline": self.com_deadline,
            "/play": self.com_play,
            "/begin": self.com_begin,
            "/stop": self.com_stop,
            "/result": self.com_result,
        }

    async def new_member(self, chat_id: int, chat_name: str, user_tg: int, name: str):
        user = await self.app.store.user_accessor.find_user_by_tg(user_tg)
        if user is None:
            user = await self.app.store.user_accessor.add_user(user_tg, name)
        
        session = await self.app.store.session_accessor.find_session_by_group(chat_id)
        if session is None:
            session = await self.app.store.session_accessor.add_session(chat_id, chat_name)
        
        if await self.app.store.user_accessor.find_usersession(session.id, user.id) is None:
            await self.app.store.user_accessor.add_usersession(session.id, user.id)
            await self.app.store.session_accessor.set_member_amount(chat_id, 1)
        
        return user

    async def command(self, message: "Message") -> BotResponse:
        command_text = message.data
        if "@" in command_text:
            command_text = command_text.split("@")[0]
        
        com = command_text.split()
        if com[0] in self.commands:
            return await self.commands[com[0]](message, com[1:])
        return BotResponse(status="error", chat_id=message.chat.id, message="Неизвестная команда")

    async def com_start(self, message: "Message", *args) -> BotResponse:
        try:
            session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
            
            if session is not None:
                if session.state == 2 or session.state == 3:
                    return BotResponse(
                        status="error", 
                        chat_id=message.chat.id, 
                        message=(
                            "Игра уже началась! Используйте /play чтобы присоединиться или /stop чтобы остановить игру."
                        )
                    )
                
                user = await self.new_member(
                    message.chat.id,
                    message.chat.title,
                    message.from_.id,
                    message.from_.first_name + " " + (message.from_.last_name or ""),
                )
                
                try:
                    await self.app.store.round_accessor.add_session_round(session.id, user.id)
                except Exception as e:
                    if "unique constraint" in str(e).lower():
                        if session.state == 0:
                            await self.app.store.session_accessor.set_session_state(session.id, 1)
                        return BotResponse(
                            status="ok", 
                            chat_id=message.chat.id, 
            message=(
                "Вы уже в игре! Используйте /play чтобы добавить других игроков или "
                "/begin чтобы начать игру."
            )
                        )
                    raise e
                
                if session.state == 0:
                    await self.app.store.session_accessor.set_session_state(session.id, 1)
                
                return BotResponse(
                    status="ok", 
                    chat_id=message.chat.id, 
                    message=(
                        "Привет! Я бот для игры в слова. Используйте /play чтобы присоединиться к игре, "
                        "/begin чтобы начать игру."
                    )
                )
            
            session = await self.app.store.session_accessor.add_session(message.chat.id, message.chat.title)
            
            user = await self.new_member(
                message.chat.id,
                message.chat.title,
                message.from_.id,
                message.from_.first_name + " " + (message.from_.last_name or ""),
            )
            
            await self.app.store.round_accessor.add_session_round(session.id, user.id)
            
            await self.app.store.session_accessor.set_session_state(session.id, 1)
            
            return BotResponse(
                status="ok", 
                chat_id=message.chat.id, 
                message=(
                    "Привет! Я бот для игры в слова. Используйте /play чтобы присоединиться к игре, "
                    "/begin чтобы начать игру."
                )
            )
            
        except Exception as e:
            return BotResponse(status="error", chat_id=message.chat.id, message=f"Ошибка: {e!s}")

    async def com_help(self, message: "Message", *args) -> BotResponse:
        help_text = """
🎯 Команды бота для игры в слова:

/start - Начать новую игру
/play - Присоединиться к игре
/begin - Начать игру (когда все игроки готовы)
/stop - Остановить игру
/result - Показать текущие результаты
/help - Показать эту справку

Как играть:
1. Используйте /start чтобы создать игру
2. Другие игроки используют /play чтобы присоединиться
3. Используйте /begin чтобы начать игру
4. Игроки по очереди называют слова на заданную букву
5. Используйте /result чтобы посмотреть результаты
6. Используйте /stop чтобы завершить игру

Удачи в игре! 🎮
        """
        return BotResponse(status="ok", chat_id=message.chat.id, message=help_text)

    async def com_deadline(self, message: "Message", *args) -> BotResponse:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        await self.app.store.session_accessor.set_session_delay(session.id, int(args[1]))
        return BotResponse(status="ok", chat_id=message.chat.id, message=f"время хода установлено на {args[1]} секунд")

    async def com_play(self, message: "Message", *args) -> BotResponse:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        if session is None:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Сначала используйте /start чтобы создать игру"
            )
        
        if session.state not in [0, 1]:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Игра уже началась! Невозможно добавить игрока."
            )
        
        user = await self.new_member(
            message.chat.id,
            message.chat.title,
            message.from_.id,
            message.from_.first_name + " " + (message.from_.last_name or ""),
        )
        try:
            await self.app.store.round_accessor.add_session_round(session.id, user.id)
            if session.state == 0:
                await self.app.store.session_accessor.set_session_state(session.id, 1)
        except Exception as e:
            if "unique constraint" in str(e).lower():
                return BotResponse(status="error", chat_id=message.chat.id, message="Вы уже в игре!")
            return BotResponse(status="error", chat_id=message.chat.id, message=f"Ошибка: {e!s}")
        return BotResponse(
            status="ok", 
            chat_id=message.chat.id, 
            message="Игрок добавлен! Используйте /begin чтобы начать игру."
        )

    async def _validate_begin_conditions(self, session, message: "Message") -> BotResponse | None:
        if session is None:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Сначала используйте /start чтобы создать игру"
            )
        
        if session.state == 0:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Сначала добавьте игроков с помощью /play"
            )
        
        if session.state in [2, 3]:
            return BotResponse(status="error", chat_id=message.chat.id, message="Игра уже началась!")
        
        if session.state != 1:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Невозможно начать игру в текущем состоянии"
            )
        
        return None

    async def com_begin(self, message: "Message", *args) -> BotResponse:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        
        error_response = await self._validate_begin_conditions(session, message)
        if error_response:
            return error_response
        
        rounds_count = await self.app.store.round_accessor.find_rounds_amount(session.id)
        if rounds_count < 2:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Недостаточно игроков! Минимум 2 игрока для начала игры."
            )
        
        order = await self.app.store.round_accessor.shaffle_session_rounds(session.id)
        if len(order) == 0:
            return BotResponse(status="error", chat_id=message.chat.id, message="Недостаточно игроков для начала игры")
        suitable_letters = [
            "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", 
            "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "э", "ю"
        ]
        char = suitable_letters[randint(0, len(suitable_letters) - 1)]
        await self.app.store.session_accessor.set_letter(session.id, char)
        await self.app.store.session_accessor.set_current_user(session.id, order[0].user_id)
        await self.app.store.session_accessor.set_session_state(session.id, 2)
        cur = await self.app.store.user_accessor.find_user_by_id(order[0].user_id)
        session = await self.app.store.session_accessor.set_last(session.id)
        return BotResponse(
            status="redirect",
            chat_id=message.chat.id,
            message=f"Игра началась!\nПервая буква: {char}\n{cur.name}, ваш ход!",
            data={"func": "timeout", "session": session.id, "user": cur.id, "delay": session.delay, "last": None},
        )

    async def com_stop(self, message: "Message", *args) -> BotResponse:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        if session is None:
            return BotResponse(status="error", chat_id=message.chat.id, message="Нет активной игры")
        if session.state == 0:
            return BotResponse(status="error", chat_id=message.chat.id, message="Нечего останавливать")
        
        res = await self.app.store.session_accessor.get_result(session.id)
        
        await self.app.store.round_accessor.clear_session_rounds(session.id)
        await self.app.store.session_accessor.del_session(session.chat_id)
        
        return BotResponse(
            status="ok",
            chat_id=message.chat.id,
            message="Игра остановлена, результаты:\n" + "\n".join(f"{el}: {res[el]}" for el in res),
        )

    async def com_result(self, message: "Message", *args) -> BotResponse:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        if session is None:
            return BotResponse(status="error", chat_id=message.chat.id, message="Нет активной игры")
        if session.state == 2 or session.state == 3:
            res = await self.app.store.session_accessor.get_result(session.id)
            return BotResponse(
                status="ok",
                chat_id=message.chat.id,
                message="Текущие результаты:\n" + "\n".join(f"{el}: {res[el]}" for el in res),
            )
        return BotResponse(status="error", chat_id=message.chat.id, message="Игра не началась")
