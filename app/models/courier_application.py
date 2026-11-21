from sqlalchemy import Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.mixins import ApplicationMixin
from app.utils.enums import TransportType


class CourierApplication(ApplicationMixin, Base):
    __tablename__ = "courier_applications"
    transport_type: Mapped[TransportType] = mapped_column(Enum(TransportType))
    experience: Mapped[str | None] = mapped_column(Text)