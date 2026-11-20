from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.utils.enums import RoleName

class User(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column( DateTime(timezone=True), server_default=func.now() )
    roles: Mapped[list["UserRole"]] = relationship( back_populates="user", cascade="all, delete-orphan" , lazy="selectin" )
    @property
    def role_names(self) -> list[RoleName]:
        return [r.role for r in self.roles]
    def has_role(self, role: RoleName) -> bool:
        return role in self.role_names

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role"),)

    id: Mapped[int] = mapped_column(primary_key = True)
    user_id: Mapped[int] = mapped_column( ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[RoleName] = mapped_column(Enum(RoleName))
    created_at: Mapped[datetime] = mapped_column( DateTime(timezone=True), server_default=func.now() )
    user: Mapped["User"] = relationship(back_populates="roles")