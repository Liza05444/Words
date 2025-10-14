import asyncio
import time
import typing

from app.store.game import BotResponse

if typing.TYPE_CHECKING:
    from app.store.bot.dataclasses import Message
    from app.web.app import Application


class GameLogic:
    GAME_STATES = ["off", "add", "step", "vote", "error"]
    VOTING_DELAY = 10
    VOTE_TIMEOUT = 3

    def __init__(self, app: "Application"):
        self.app = app

    def get_next_letter(self, word: str) -> str:
        if not word or len(word) == 0:
            return ""
        
        word_lower = word.lower()
        
        for i in range(len(word_lower) - 1, -1, -1):
            char = word_lower[i]
            if char not in ['ь', 'ъ', 'ы']:
                return char
        
        return word_lower[-1]

    async def process_user_vote(self, message: "Message") -> None:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        user = await self.app.store.user_accessor.find_user_by_tg(message.from_.id)
        
        if session is None or user is None:
            return
            
        if message.data and message.data.startswith("uncorrect_") and session.state == self.VOTE_TIMEOUT:
                word_id = message.data.replace("uncorrect_", "")
                if session.last == word_id:
                    await self.app.store.round_accessor.set_vote(session.id, user.id)

    async def evaluate_word(self, chat_id: int, session_id: int, word: str, word_id: str | None = None) -> BotResponse:
        await asyncio.sleep(self.VOTING_DELAY)
        
        session = await self.app.store.session_accessor.find_session_by_id(session_id)
        if session is None:
            return BotResponse(
                status="pass",
                chat_id=chat_id,
                message="Игра была остановлена",
            )
        
        await self.app.store.session_accessor.set_session_state(session_id, 2)
        
        vote_result = await self.app.store.round_accessor.count_votes(session_id)
        await self.app.store.round_accessor.reset_votes(session_id)
        
        if not vote_result:
            session = await self.app.store.session_accessor.find_session_by_id(session_id)
            await self.app.store.session_accessor.set_session_state(session_id, 2)
            return BotResponse(
                status="ok",
                chat_id=chat_id,
                message="Слово не принято участниками. Попробуйте другое слово.",
            )
        
        await self.app.store.round_accessor.add_word(session_id, word)
        round_data = await self.app.store.round_accessor.find_current_round(session_id)
        
        if round_data is None:
            return BotResponse(
                status="error",
                chat_id=chat_id,
                message="Ошибка в данных раунда. Игра прервана.",
            )
        
        session = await self.app.store.session_accessor.set_current_user(session_id, round_data.next)
        next_letter = self.get_next_letter(word)
        await self.app.store.session_accessor.set_letter(session.id, next_letter)
        user = await self.app.store.user_accessor.find_user_by_id(session.current_user)
        session = await self.app.store.session_accessor.set_last(session.id, word)
        
        return BotResponse(
            status="redirect",
            chat_id=session.chat_id,
            message=f"Слово принято!\nСледующая буква: {next_letter}\n{user.name}, ваш ход",
            data={
                "func": "timeout", 
                "session": session.id, 
                "user": user.id, 
                "delay": session.delay, 
                "last": word
            },
        )

    async def handle_timeout(self, session_id: int, user_id: int, delay: int, last: str | None) -> BotResponse:
        await asyncio.sleep(delay)
        session = await self.app.store.session_accessor.find_session_by_id(session_id)
        
        if session is None:
            return BotResponse(
                status="pass",
                chat_id=0, 
                message="Игра была остановлена",
            )
        
        if last != session.last:
            return BotResponse(
                status="pass",
                chat_id=session.chat_id,
                message="Ход уже сделан",
            )
        
        eliminated_user = await self.app.store.user_accessor.find_user_by_id(user_id)
        results = await self.app.store.session_accessor.get_result(session_id)
        
        next_user_id = await self.app.store.round_accessor.find_next_user_after_elimination(session_id, user_id)
        
        if next_user_id is None:
            await self.app.store.session_accessor.set_session_state(session.id, 0)
            await self.app.store.round_accessor.clear_session_rounds(session.id)
            return BotResponse(
                status="ok",
                chat_id=session.chat_id,
                message="Игра завершена - не осталось игроков",
            )
        
        remaining_players = await self.app.store.round_accessor.del_session_round(session_id, user_id)
        
        session = await self.app.store.session_accessor.set_current_user(session_id, next_user_id)
        next_user = await self.app.store.user_accessor.find_user_by_id(next_user_id)
        
        if remaining_players == 1:
            await self.app.store.session_accessor.set_session_state(session.id, 0)
            await self.app.store.round_accessor.clear_session_rounds(session.id)
            return BotResponse(
                status="ok",
                chat_id=session.chat_id,
                message=f"Игра окончена! {next_user.name} победил!\nРезультаты:\n" + 
                       "\n".join(f"{player}: {score}" for player, score in results.items()),
            )
        
        return BotResponse(
            status="ok",
            chat_id=session.chat_id,
            message=f"Время вышло! {eliminated_user.name} выбывает (очки: {results[eliminated_user.name]})\n"
                   f"{next_user.name}, ваш ход\nБуква: {session.letter}",
        )

    async def _validate_word_input(self, message: "Message", session, user) -> BotResponse | None:
        if session is None:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Нет активной игры. Используйте /start чтобы начать новую игру."
            )
        
        if user is None:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Пользователь не найден. Используйте /start чтобы зарегистрироваться."
            )
        
        if session.current_user != user.id:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Не ваш ход, подождите"
            )
        
        if session.state != 2:
            error_msg = ("Вы уже отправили слово! Ждите вердикта участников." 
                        if session.state == self.VOTE_TIMEOUT 
                        else "Игра не в состоянии хода. Подождите.")
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message=error_msg
            )
        
        if not message.data:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Сообщение пустое"
            )
        
        return None

    async def _validate_word_content(self, word: str, session, message: "Message") -> BotResponse | None:
        if not word:
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Слово не может быть пустым"
            )
        
        if not word.isalpha():
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Слово должно содержать только буквы"
            )
        
        if session.letter.lower() != word[0].lower():
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message=f"Неверная буква. Нужна: {session.letter}"
            )
        
        if await self.app.store.round_accessor.find_word(session.id, word):
            return BotResponse(
                status="error", 
                chat_id=message.chat.id, 
                message="Это слово уже использовалось"
            )
        
        return None

    async def process_user_word(self, message: "Message") -> BotResponse:
        session = await self.app.store.session_accessor.find_session_by_group(message.chat.id)
        user = await self.app.store.user_accessor.find_user_by_tg(message.from_.id)
        
        error_response = await self._validate_word_input(message, session, user)
        if error_response:
            return error_response
        
        word = message.data.strip()
        
        error_response = await self._validate_word_content(word, session, message)
        if error_response:
            return error_response
        await self.app.store.session_accessor.set_session_state(session.id, self.VOTE_TIMEOUT)
        word_id = f"{session.id}_{int(time.time())}"
        
        await self.app.store.session_accessor.set_last(session.id, word_id)
        
        return BotResponse(
            status="redirect",
            chat_id=message.chat.id,
            message="Правильно ли это слово?",
            reply_markup={"inline_keyboard": [[{"text": "Неправильно", "callback_data": f"uncorrect_{word_id}"}]]},
            data={
                "func": "verdict",
                "session": session.id,
                "word": word,
                "word_id": word_id,
            },
        )
