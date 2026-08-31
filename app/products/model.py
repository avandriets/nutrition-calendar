from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    brand = Column(String(200), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    barcode = Column(String(64), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Пищевая ценность на 100 г продукта.
    calories_kcal = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    carbohydrates_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
