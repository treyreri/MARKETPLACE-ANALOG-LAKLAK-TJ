from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Product(Base):
    
    @property
    def image_url(self) -> str | None:
        return f"/{self.image}" if self.image else None

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True )
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(default=0)
    image: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now() )

    seller: Mapped["User"] = relationship(back_populates="products")
    category: Mapped["Category"] = relationship(back_populates="products")


#CheckConstraint: даже если API пропустит отрицательную цену, база её не примет. Это вторая линия защиты
#ondelete="RESTRICT" у категории: база запретит удалить категорию, пока в ней есть товары
#TYPE_CHECKING нужен только для подсказок редактора. Так нет циклических импортов.
