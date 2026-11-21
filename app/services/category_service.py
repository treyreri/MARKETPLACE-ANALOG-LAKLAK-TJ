from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryNotFoundError(Exception):
    pass

class CategoryNameTakenError(Exception):
    pass

def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.id)))


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError
    return category


def _ensure_names_unique(
    db: Session,
    name_ru: str | None,
    name_en: str | None,
    exclude_id: int | None = None, ) -> None:
    conditions = []
    if name_ru:
        conditions.append(Category.name_ru == name_ru)
    if name_en:
        conditions.append(Category.name_en == name_en)
    if not conditions:
        return

    stmt = select(Category.id).where(or_(*conditions))
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise CategoryNameTakenError


def create_category(db: Session, data: CategoryCreate) -> Category:
    _ensure_names_unique(db, data.name_ru, data.name_en)
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    # exclude_none: явный null для name_ru/name_en просто игнорируется
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    _ensure_names_unique(
        db, updates.get("name_ru"), updates.get("name_en"), exclude_id=category_id )
    for field, value in updates.items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    db.delete(category)
    db.commit()

#exclude_unset=True - это суть PATCH: обновляются только поля, которые клиент действительно прислал