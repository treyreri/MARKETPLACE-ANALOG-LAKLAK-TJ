from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.product import Product


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True  )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now() )

    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CartItem.id", )

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def total_price(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0"))

    @property
    def can_checkout(self) -> bool:
        return bool(self.items) and all(item.is_valid for item in self.items)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),  )

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE") )
    quantity: Mapped[int]

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(lazy="joined")

    @property
    def line_total(self) -> Decimal:
        return self.product.price * self.quantity

    @property
    def is_valid(self) -> bool:
        return self.product.is_active and self.quantity <= self.product.quantity