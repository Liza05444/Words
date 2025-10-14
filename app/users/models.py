from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_db import BaseModel


class PlayerModel(BaseModel):
    """Модель игрока в системе."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    telegram_id = Column(BigInteger, unique=True)
    name = Column(String)

    admin = relationship("GameAdminModel", back_populates="user", cascade="all, delete")
    user_sessions = relationship("PlayerSessionModel", back_populates="player", cascade="all, delete")
    rounds = relationship("GameRoundModel", back_populates="user", cascade="all, delete")


class GameSessionModel(BaseModel):
    """Модель игровой сессии."""
    __tablename__ = "sessions"
    
    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    chat_id = Column(BigInteger, unique=True)
    chat_name = Column(String)
    state = Column(Integer, default=0)
    member_amount = Column(BigInteger)
    current_user = Column(BigInteger)
    letter = Column(String(1))
    delay = Column(Integer, default=60)
    last = Column(String)

    admin = relationship("GameAdminModel", back_populates="session")
    user_sessions = relationship("PlayerSessionModel", back_populates="session", cascade="all, delete")
    rounds = relationship("GameRoundModel", back_populates="session", cascade="all, delete")


class PlayerSessionModel(BaseModel):
    """Модель связи игрока и сессии."""
    __tablename__ = "usersessions"
    
    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    user_id = Column(
        BigInteger, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    session_id = Column(
        BigInteger, 
        ForeignKey("sessions.id", ondelete="CASCADE"), 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "session_id", name="unique_player_session"),
    )

    player = relationship("PlayerModel", back_populates="user_sessions")
    session = relationship("GameSessionModel", back_populates="user_sessions")
