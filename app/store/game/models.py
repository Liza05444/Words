from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_db import BaseModel


class GameRoundModel(BaseModel):
    """Модель игрового раунда."""
    __tablename__ = "rounds"
    
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
    vote = Column(Boolean, default=False, nullable=False)
    next = Column(Integer, default=0)
    state = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "session_id", name="unique_user_session_round"),
    )

    user = relationship("PlayerModel", back_populates="rounds")
    session = relationship("GameSessionModel", back_populates="rounds")
    words = relationship("GameWordModel", back_populates="round", cascade="all, delete")


class GameWordModel(BaseModel):
    """Модель игрового слова."""
    __tablename__ = "words"
    
    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    round_id = Column(
        BigInteger, 
        ForeignKey("rounds.id", ondelete="CASCADE"), 
        nullable=False
    )
    word = Column(String, nullable=False)

    round = relationship("GameRoundModel", back_populates="words")
