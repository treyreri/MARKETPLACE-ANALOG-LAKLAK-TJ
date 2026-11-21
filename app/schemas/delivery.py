from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.user import User
from app.schemas.order import OrderItemRead
from app.utils.enums import DeliveryStatus, OrderStatus, PaymentMethod, TransportType


class CourierAssign(BaseModel):
    courier_id: int


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus


class CourierInfo(BaseModel):
    id: int
    name: str
    phone_number: str
    transport_type: TransportType | None

    @classmethod
    def from_model(cls, user: User) -> "CourierInfo":
        profile = user.courier_profile
        full_name = " ".join(filter(None, [user.first_name, user.last_name]))
        return cls(
            id=user.id,
            name=full_name or f"Courier #{user.id}",
            phone_number=profile.phone_number if profile else user.phone_number,
            transport_type=profile.transport_type if profile else None, )


class CourierOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    delivery_status: DeliveryStatus
    recipient_name: str
    phone_number: str
    address: str
    comment: str | None
    payment_method: PaymentMethod
    total_price: Decimal
    assigned_at: datetime
    delivered_at: datetime | None
    items: list[OrderItemRead]