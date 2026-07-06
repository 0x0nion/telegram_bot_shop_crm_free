# database/models/temp_models.py
from typing import Optional
from sqlalchemy import String, Text, Numeric, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base


class TempCategory(Base):
    __tablename__ = "temp_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Сохраняем оригинальный ID, чтобы при сохранении знать, что обновлять
    original_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    # ID админа, чьи правки сейчас хранятся здесь
    admin_id: Mapped[int] = mapped_column(BigInteger)


class TempProduct(Base):
    __tablename__ = "temp_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    image_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    admin_id: Mapped[int] = mapped_column(BigInteger)