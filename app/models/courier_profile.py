from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.utils.enums import TransportType

if TYPE_CHECKING:
    from app.models.user import User


class CourierProfile(Base):
    __tablename__ = "courier_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True  )
    phone_number: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(255))
    transport_type: Mapped[TransportType] = mapped_column(Enum(TransportType))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()  )

    user: Mapped["User"] = relationship(back_populates="courier_profile")