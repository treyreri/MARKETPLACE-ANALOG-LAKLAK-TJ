from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.mixins import ApplicationMixin


class SellerApplication(ApplicationMixin, Base):
    __tablename__ = "seller_applications"
    store_name: Mapped[str] = mapped_column(String(100))
    store_description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL") )