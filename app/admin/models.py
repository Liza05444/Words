from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_db import BaseModel


class GameAdminModel(BaseModel):
    """Модель администратора игровой сессии."""
    __tablename__ = "admins"
    
    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    user_id = Column(
        BigInteger, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    session_id = Column(
        BigInteger, 
        ForeignKey("sessions.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )

    user = relationship("PlayerModel", back_populates="admin")
    session = relationship("GameSessionModel", back_populates="admin")

    def __str__(self) -> str:
        return f"Admin ID: {self.id}, User ID: {self.user_id}"


class WebAdminModel(BaseModel):
    """Модель веб-администратора системы."""
    __tablename__ = "webadmins"
    
    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    email = Column(String, unique=True)
    password = Column(String, unique=True)

    def __repr__(self) -> str:
        return f"WebAdmin(email={self.email})"
