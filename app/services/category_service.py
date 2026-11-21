from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryNotFoundError(Exception):
    pass

class CategoryNameTakenError(Exception):
    pass


class CategoryInUseError(Exception):
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
    # null for name_ru/name_en is rejected by the schema; description may be cleared
    updates = data.model_dump(exclude_unset=True)
    _ensure_names_unique(
        db, updates.get("name_ru"), updates.get("name_en"), exclude_id=category_id )
    for field, value in updates.items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


#exclude_unset=True - это суть PATCH: обновляются только поля, которые клиент действительно прислал


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    has_products = db.scalar(
        select(Product.id).where(Product.category_id == category_id).limit(1) )
    if has_products is not None:
        raise CategoryInUseError
    db.delete(category)
    db.commit()