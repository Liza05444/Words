import base64
import typing

from sqlalchemy import select

from app.admin.models import WebAdminModel
from app.store.database.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class WebAdminAccessor(BaseAccessor):
    async def connect(self, app: "Application" = None) -> None:
        if self.app is None:
            self.app = app
        async with self.app.database.session() as session:
            stml = select(WebAdminModel).where(WebAdminModel.email == app.config.admin.email)
            result = await session.execute(stml)
            admin: WebAdminModel = result.scalar()
            if admin is None or admin.password != base64.b64encode(app.config.admin.password.encode()).decode():
                session.add(
                    WebAdminModel(
                        email=app.config.admin.email,
                        password=base64.b64encode(app.config.admin.password.encode()).decode(),
                    )
                )
                await session.commit()

    async def get_by_email(self, email: str) -> WebAdminModel | None:
        async with self.app.database.session() as session:
            async with session.begin():
                res = await session.execute(select(WebAdminModel).where(WebAdminModel.email == email))
                admin = res.scalar()
        return admin

    async def create_admin(self, email: str, password: str) -> WebAdminModel:
        admin = WebAdminModel(email=email, password=base64.b64encode(password.encode()).decode())
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(admin)
                await session.commit()
        return admin
