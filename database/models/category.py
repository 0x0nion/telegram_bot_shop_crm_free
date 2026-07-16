# database/models/category.py
from typing import Optional, List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey(column= "categories.id", ondelete="CASCADE"))
    subcategories: Mapped[List["Category"]] = relationship(argument="Category", back_populates="parent")
    parent: Mapped[Optional["Category"]] = relationship(argument="Category", remote_side=[id], back_populates="subcategories")

    products: Mapped[List["Product"]] = relationship(argument="Product", back_populates="category")

