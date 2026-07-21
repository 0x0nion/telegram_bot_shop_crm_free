from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    # Это поле остается для специфических, единых для всех локалей данных
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    price: Mapped[float] = mapped_column(Numeric(10, 2))
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    image_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")