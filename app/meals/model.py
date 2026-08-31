from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_date = Column(Date, nullable=False, index=True)
    meal_type = Column(String(20), nullable=False)
    name = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("Account", back_populates="meals")
    rows = relationship(
        "MealRow",
        back_populates="meal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MealRow.position",
    )


class MealRow(Base):
    __tablename__ = "meal_rows"
    __table_args__ = (
        UniqueConstraint("meal_id", "product_id"),
        UniqueConstraint("meal_id", "position"),
    )

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    position = Column(Integer, nullable=False)

    # Snapshot keeps historical nutrition stable if the catalogue product changes.
    product_name = Column(String(200), nullable=False)
    product_brand = Column(String(200), nullable=True)
    calories_kcal = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    carbohydrates_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    meal = relationship("Meal", back_populates="rows")
    portions = relationship(
        "MealEntry",
        back_populates="row",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MealEntry.user_id",
    )


class MealEntry(Base):
    __tablename__ = "meal_entries"
    __table_args__ = (UniqueConstraint("meal_row_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    meal_row_id = Column(Integer, ForeignKey("meal_rows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_g = Column(Float, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    row = relationship("MealRow", back_populates="portions")

    __mapper_args__ = {"version_id_col": version}
