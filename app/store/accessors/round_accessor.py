from random import shuffle

from sqlalchemy import Sequence, and_, case, delete, func, select, update

from app.store.database.base_accessor import BaseAccessor
from app.store.game.models import GameRoundModel, GameWordModel
from app.users.models import GameSessionModel, PlayerModel


class RoundAccessor(BaseAccessor):
    async def find_rounds_by_user_id(self, tg_id: int) -> Sequence[GameRoundModel]:
        stmp = (
            select(GameRoundModel)
            .select_from(PlayerModel)
            .join(GameRoundModel, PlayerModel.id == GameRoundModel.id)
            .where(PlayerModel.telegram_id == tg_id)
        )
        async with self.app.database.session() as session:
            return (await session.execute(stmp)).scalars().all()

    async def find_rounds_amount(self, session_id: int) -> int:
        stmp = select(func.count(1)).select_from(GameRoundModel).where(GameRoundModel.session_id == session_id)
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_current_round(self, session_id: int) -> GameRoundModel | None:
        stmp = (
            select(GameRoundModel)
            .select_from(GameSessionModel)
            .join(GameRoundModel)
            .where(and_(
                GameRoundModel.session_id == session_id, 
                GameRoundModel.user_id == GameSessionModel.current_user
            ))
        )
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_next_user_after_elimination(self, session_id: int, eliminated_user_id: int) -> int | None:
        """Находит следующего игрока после исключения."""
        stmp = select(GameRoundModel).where(GameRoundModel.session_id == session_id)
        async with self.app.database.session() as session:
            rounds = (await session.scalars(stmp)).all()
            
            if not rounds:
                return None
                
            eliminated_round = None
            for round_obj in rounds:
                if round_obj.user_id == eliminated_user_id:
                    eliminated_round = round_obj
                    break
            
            if eliminated_round is None:
                return rounds[0].user_id if rounds else None
                
            return eliminated_round.next

    async def find_word(self, session_id: int, text: str) -> GameWordModel | None:
        stmp = (
            select(GameWordModel)
            .select_from(GameRoundModel)
            .join(GameWordModel)
            .where(and_(GameRoundModel.session_id == session_id, func.lower(GameWordModel.word) == text.lower()))
        )
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def add_word(self, session_id: int, text: str) -> GameWordModel:
        row = await self.find_current_round(session_id)
        word = GameWordModel(round_id=row.id, word=text.lower())
        async with self.app.database.session() as session:
            session.add(word)
            await session.commit()
        return word

    async def set_vote(self, session_id: int, user_id: int) -> bool:
        stmp = (
            update(GameRoundModel)
            .where(and_(GameRoundModel.session_id == session_id, GameRoundModel.user_id == user_id))
            .values(vote=True)
        )
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def count_votes(self, session_id: int) -> bool:
        stmp = (
            select(GameRoundModel.vote, func.count(GameRoundModel.vote))
            .where(GameRoundModel.session_id == session_id)
            .group_by(GameRoundModel.vote)
        )
        async with self.app.database.session() as session:
            res = (await session.execute(stmp)).all()
        out = [0, 0]
        for i, n in res:
            out[i] = n
        return out[0] - 1 > out[1]

    async def reset_votes(self, session_id: int) -> bool:
        stmp = update(GameRoundModel).where(GameRoundModel.session_id == session_id).values(vote=0)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def add_session_round(self, session_id: int, user_id: int) -> GameRoundModel:
        row = GameRoundModel(user_id=user_id, session_id=session_id, state=0)
        async with self.app.database.session() as session:
            session.add(row)
            await session.commit()
        return row

    async def del_session_round(self, session_id: int, user_id: int) -> int:
        async with self.app.database.session() as session:
            qsel = select(GameRoundModel).where(and_(
                GameRoundModel.session_id == session_id, 
                GameRoundModel.user_id == user_id
            ))
            row = await session.scalar(qsel)
            
            if row is None:
                return await self.find_rounds_amount(session_id)
            
            qset = (
                update(GameRoundModel)
                .where(and_(GameRoundModel.session_id == session_id, GameRoundModel.next == row.user_id))
                .values(next=row.next)
            )
            await session.execute(qset)
            
            qdel = delete(GameRoundModel).where(GameRoundModel.id == row.id)
            await session.execute(qdel)
            await session.commit()
            
        return await self.find_rounds_amount(session_id)

    async def shaffle_session_rounds(self, session_id: int) -> list[GameRoundModel]:
        get_rows = select(GameRoundModel).where(GameRoundModel.session_id == session_id)
        async with self.app.database.session() as session:
            res = (await session.scalars(get_rows)).all()
            rounds = list(res)
            if len(rounds) < 2:
                return []
            shuffle(rounds)
            updates = case(
                *[(GameRoundModel.user_id == rounds[i].user_id, rounds[i - 1].user_id) for i in range(len(rounds))],
                else_=GameRoundModel.next,
            )
            set_rows = update(GameRoundModel).where(GameRoundModel.session_id == session_id).values(next=updates)
            await session.execute(set_rows)
            await session.commit()
        return rounds

    async def clear_session_rounds(self, session_id: int) -> bool:
        stmp = delete(GameRoundModel).where(GameRoundModel.session_id == session_id)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True
