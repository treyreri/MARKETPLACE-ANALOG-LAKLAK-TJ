from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.user import PhoneNumber
from app.utils.enums import OrderStatus, PaymentMethod


class OrderCreate(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=100)
    phone_number: PhoneNumber
    address: str = Field(min_length=1, max_length=255)
    comment: str | None = Field(default=None, max_length=1000)
    payment_method: PaymentMethod = PaymentMethod.CASH_ON_DELIVERY


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int | None
    product_name: str
    price: Decimal
    quantity: int
    line_total: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: OrderStatus
    recipient_name: str
    phone_number: str
    address: str
    comment: str | None
    payment_method: PaymentMethod
    total_price: Decimal
    courier_id: int | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class SellerOrderRead(BaseModel):
    order_id: int
    status: OrderStatus
    created_at: datetime
    items: list[OrderItemRead]
    total: Decimal

    @classmethod
    def from_items(cls, order: Order, items: list[OrderItem]) -> "SellerOrderRead":
        return cls(
            order_id=order.id,
            status=order.status,
            created_at=order.created_at,
            items=[OrderItemRead.model_validate(item) for item in items],
            total=sum((item.line_total for item in items), Decimal("0")),  )