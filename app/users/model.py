from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class AccountUser(Base):
    __tablename__ = "account_users"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    birth_date = Column(Date, nullable=True)
    height_cm = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("Account", back_populates="users")
    goals = relationship("UserGoal", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    measurements = relationship("BodyMeasurement", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


class UserGoal(Base):
    __tablename__ = "user_goals"
    __table_args__ = (UniqueConstraint("user_id", "effective_from"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="CASCADE"), nullable=False, index=True)
    daily_calories_kcal = Column(Float, nullable=False)
    daily_protein_g = Column(Float, nullable=False)
    daily_fiber_g = Column(Float, nullable=False)
    effective_from = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("AccountUser", back_populates="goals")


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"
    __table_args__ = (UniqueConstraint("user_id", "measured_on"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="CASCADE"), nullable=False, index=True)
    measured_on = Column(Date, nullable=False, default=date.today)
    weight_kg = Column(Float, nullable=True)
    neck_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("AccountUser", back_populates="measurements")
