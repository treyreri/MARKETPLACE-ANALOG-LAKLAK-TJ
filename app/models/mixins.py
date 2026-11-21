from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, Text, func
from app.models.types import UTCDateTime
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from app.utils.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.user import User


class ApplicationMixin:
    """Common fields for seller and courier applications."""

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    phone_number: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(255))
    additional_info: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True )
    admin_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now() )
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship()


#@declared_attr нужен для ForeignKey и relationship. 
#Он заставляет SQLAlchemy создавать отдельный объект для каждой таблицы, а не один общий на обе