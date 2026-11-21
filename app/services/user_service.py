from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.utils.enums import RoleName


class UserNotFoundError(Exception):
    pass


class CannotBlockSelfError(Exception):
    pass


def list_users(
    db: Session,
    q: str | None = None,
    role: RoleName | None = None,
    is_active: bool | None = None,
    limit: int = 20,
    offset: int = 0, ) -> tuple[list[User], int]:
    stmt = select(User)
    query = (q or "").strip()
    if query:
        lowered = query.lower()
        stmt = stmt.where(or_(
            User.phone_number.contains(query.replace(" ", ""), autoescape=True),
            func.lower(User.first_name).contains(lowered, autoescape=True),
            func.lower(User.last_name).contains(lowered, autoescape=True), ))
    if role is not None:
        stmt = stmt.where(User.roles.any(UserRole.role == role))
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(User.id.desc()).limit(limit).offset(offset))
    return list(items), total


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError
    return user


def set_active(db: Session, admin: User, user_id: int, is_active: bool) -> User:
    """Block/unblock. Blocked users cannot log in, their tokens stop working
    and their products disappear from the catalog."""
    user = get_user(db, user_id)
    if user.id == admin.id and not is_active:
        raise CannotBlockSelfError
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
