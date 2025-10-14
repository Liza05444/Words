from sqlalchemy import Sequence, delete, func, select, update

from app.admin.models import GameAdminModel
from app.store.database.base_accessor import BaseAccessor
from app.store.game.models import GameRoundModel, GameWordModel
from app.users.models import GameSessionModel, PlayerModel, PlayerSessionModel


class SessionAccessor(BaseAccessor):
    async def find_session_by_user_tg(self, tg_id: int) -> Sequence[GameSessionModel]:
        stmp = (
            select(GameSessionModel)
            .select_from(PlayerModel)
            .join(PlayerSessionModel)
            .join(GameSessionModel)
            .where(PlayerModel.telegram_id == tg_id)
        )
        async with self.app.database.session() as session:
            return (await session.execute(stmp)).scalars().all()

    async def find_session_by_id(self, session_id: int) -> GameSessionModel:
        stmp = select(GameSessionModel).where(GameSessionModel.id == session_id)
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_session_by_group(self, chat_id: int) -> GameSessionModel:
        stmp = select(GameSessionModel).where(GameSessionModel.chat_id == chat_id)
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_session_by_admin(self, admin_tg: int) -> Sequence[GameSessionModel]:
        stmp = (
            select(GameSessionModel)
            .join(GameAdminModel)
            .join(PlayerModel)
            .where(PlayerModel.telegram_id == admin_tg)
        )
        async with self.app.database.session() as session:
            return (await session.scalars(stmp)).all()

    async def set_session_state(self, session_id: int, state: int) -> bool:
        stmp = update(GameSessionModel).where(GameSessionModel.id == session_id).values(state=state)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def set_member_amount(self, chat_id: int, amount: int) -> bool:
        async with self.app.database.session() as session:
            qget = select(GameSessionModel).where(GameSessionModel.chat_id == chat_id)
            ses = await session.scalar(qget)
            qset = (
                update(GameSessionModel)
                .where(GameSessionModel.id == ses.id)
                .values(member_amount=ses.member_amount + amount)
            )
            await session.execute(qset)
            await session.commit()
        return True

    async def set_session_delay(self, session_id: int, delay: int) -> bool:
        stmp = update(GameSessionModel).where(GameSessionModel.id == session_id).values(delay=delay)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def set_letter(self, session_id: int, letter: str) -> bool:
        stmp = update(GameSessionModel).where(GameSessionModel.id == session_id).values(letter=letter)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def set_current_user(self, session_id: int, user_id: int) -> GameSessionModel:
        stmp = update(GameSessionModel).where(GameSessionModel.id == session_id).values(current_user=user_id)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return await self.find_session_by_id(session_id)

    async def set_last(self, session_id: int, last: str | None = None) -> GameSessionModel:
        stmp = update(GameSessionModel).where(GameSessionModel.id == session_id).values(last=last)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return await self.find_session_by_id(session_id)

    async def add_session(self, chat_id: int, chat_name: str) -> GameSessionModel:
        existing_session = await self.find_session_by_group(chat_id)
        if existing_session is not None:
            return existing_session
        
        ses = GameSessionModel(chat_id=chat_id, chat_name=chat_name, state=0, member_amount=1, letter="-", last="")
        async with self.app.database.session() as session:
            session.add(ses)
            await session.commit()
        return ses

    async def del_session(self, session_id: int) -> bool:
        stmp = delete(GameSessionModel).where(GameSessionModel.chat_id == session_id)
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def get_result(self, session_id: int) -> dict[str, int]:
        stmp = (
            select(PlayerModel.name, func.count(GameWordModel.round_id).label("count"))
            .select_from(PlayerModel)
            .join(GameRoundModel)
            .join(GameWordModel, full=True)
            .where(GameRoundModel.session_id == session_id)
            .group_by(PlayerModel.name)
        )
        async with self.app.database.session() as session:
            rs = await session.execute(stmp)
        return dict(rs.all())
