from sqlalchemy import Sequence, and_, delete, select

from app.admin.models import GameAdminModel
from app.store.database.base_accessor import BaseAccessor
from app.users.models import GameSessionModel, PlayerModel, PlayerSessionModel


class UserAccessor(BaseAccessor):
    async def find_user_by_id(self, user_id: int) -> PlayerModel:
        stmp = select(PlayerModel).where(PlayerModel.id == user_id)
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_user_by_tg(self, tg_id: int) -> PlayerModel:
        stmp = select(PlayerModel).where(PlayerModel.telegram_id == tg_id)
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_admin_by_tg(self, tg_id: int) -> PlayerModel:
        stmp = select(PlayerModel).select_from(GameAdminModel).join(PlayerModel).where(PlayerModel.telegram_id == tg_id)
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def find_usersession(self, session_id: int, user_id: int) -> PlayerSessionModel:
        stmp = select(PlayerSessionModel).where(
            and_(PlayerSessionModel.user_id == user_id, PlayerSessionModel.session_id == session_id)
        )
        async with self.app.database.session() as session:
            return await session.scalar(stmp)

    async def add_user(self, id: int, name: str) -> PlayerModel:
        user = PlayerModel(telegram_id=id, name=name)
        async with self.app.database.session() as session:
            session.add(user)
            await session.commit()
        return user

    async def del_user(self, user_id: int) -> bool:
        stmp = delete(PlayerModel).where(PlayerModel.id == user_id)
        async with self.app.database.session() as session:
            await session.execute(stmp)
        return True

    async def add_admin(self, user_id: int, session_id: int) -> GameAdminModel:
        admin = GameAdminModel(user_id=user_id, session_id=session_id)
        async with self.app.database.session() as session:
            session.add(admin)
            await session.commit()
        return admin

    async def del_admin(self, session_id: int) -> bool:
        stmp = delete(PlayerModel).where(GameAdminModel.session_id == session_id)
        async with self.app.database.session() as session:
            await session.execute(stmp)
        return True

    async def add_usersession(self, session_id: int, user_id: int) -> PlayerSessionModel:
        us = PlayerSessionModel(user_id=user_id, session_id=session_id)
        async with self.app.database.session() as session:
            session.add(us)
            await session.commit()
        return us

    async def del_usersession(self, session_id: int, user_id: int) -> bool:
        stmp = delete(PlayerSessionModel).where(
            and_(PlayerSessionModel.user_id == user_id, PlayerSessionModel.session_id == session_id)
        )
        async with self.app.database.session() as session:
            await session.execute(stmp)
            await session.commit()
        return True

    async def get_users(self, session_id: int) -> Sequence[PlayerModel]:
        stmp = (
            select(PlayerModel)
            .select_from(GameSessionModel)
            .join(PlayerSessionModel)
            .join(PlayerModel)
            .where(GameSessionModel.id == session_id)
        )
        async with self.app.database.session() as session:
            return (await session.scalars(stmp)).all()
