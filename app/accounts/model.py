from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship(
        "AccountUser",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    meals = relationship(
        "Meal",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
