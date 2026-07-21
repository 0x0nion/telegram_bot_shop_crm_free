# database/models/temp_models.py
from typing import Optional
from sqlalchemy import String, Text, Numeric, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base


class TempCategory(Base):
    __tablename__ = "temp_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[Optional[int]] = mapped_column(nullable=True)
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


class TempLocaleText(Base):
    __tablename__ = "temp_locale_texts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Ссылка на временную сущность (например, TempProduct.id или TempCategory.id)
    temp_entity_id: Mapped[int] = mapped_column(index=True)
    # Тип: 'temp_category' или 'temp_product'
    entity_type: Mapped[str] = mapped_column(String(50))

    language_code: Mapped[str] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text)

    admin_id: Mapped[int] = mapped_column(BigInteger, index=True)

    __table_args__ = (
        UniqueConstraint("temp_entity_id", "entity_type", "language_code", "admin_id", name="uq_temp_locale"),
    )

