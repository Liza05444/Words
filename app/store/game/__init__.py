import typing

from app.store.game.dataclasses import BotResponse

if typing.TYPE_CHECKING:
    from app.store.bot.dataclasses import UpdateObj
    from app.web.app import Application


class Game:
    def __init__(self, app: "Application"):
        from app.store.game.game_commands import GameCommands
        from app.store.game.game_events import GameEvents
        from app.store.game.game_logic import GameLogic

        self.logic = GameLogic(app)
        self.commands = GameCommands(app)
        self.events = GameEvents(app)

    async def handle(self, upd: "UpdateObj") -> BotResponse:
        try:
            if upd.status == "message":
                if upd.message.data and upd.message.data.startswith("/"):
                    return await self.commands.command(upd.message)
                return await self.logic.process_user_word(upd.message)
            if upd.status == "callback":
                await self.logic.process_user_vote(upd.message)
                return BotResponse(
                    status="pass",
                    message="Голос обработан",
                    chat_id=upd.message.chat.id,
                )
            if upd.status == "member":
                await self.events.event(upd.message)
                return BotResponse(
                    status="pass",
                    message="Событие обработано",
                    chat_id=upd.message.chat.id,
                )
            return BotResponse(
                status="pass",
                message="обработано",
                chat_id=upd.message.chat.id,
            )
        except Exception as e:
            return BotResponse(
                status="error",
                message=f"Ошибка обработки: {e!s}",
                chat_id=upd.message.chat.id,
            )

    async def delay_handler(self, ans: BotResponse) -> BotResponse:
        if ans.data.get("func") == "verdict":
            return await self.logic.evaluate_word(
                ans.chat_id, ans.data["session"], ans.data["word"], ans.data.get("word_id")
            )
        if ans.data.get("func") == "timeout":
            return await self.logic.handle_timeout(
                ans.data["session"], ans.data["user"], ans.data["delay"], ans.data["last"]
            )
        return BotResponse(status="pass", message="функция не существует", chat_id=ans.chat_id)
