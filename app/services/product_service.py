from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload
from app.models.category import Category
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductFilters, ProductUpdate
from app.services import category_service
from app.utils.enums import OrderStatus, ProductSort
from app.utils.files import delete_file, save_product_image


class ProductNotFoundError(Exception):
    pass


SORT_ORDER = {
    ProductSort.NEWEST: Product.created_at.desc(),
    ProductSort.PRICE_ASC: Product.price.asc(),
    ProductSort.PRICE_DESC: Product.price.desc(), }


def _units_sold_subquery():
    """Units sold per product, ignoring cancelled orders."""
    return (
        select(OrderItem.product_id, func.sum(OrderItem.quantity).label("units_sold"))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != OrderStatus.CANCELLED, OrderItem.product_id.is_not(None))
        .group_by(OrderItem.product_id)
        .subquery() )


def _apply_filters(stmt, filters: ProductFilters):
    """Text search and filters; stmt must already join Category."""
    query = (filters.q or "").strip().lower()
    if query:
        stmt = stmt.where( or_(
                func.lower(Product.name).contains(query, autoescape=True),
                func.lower(Product.description).contains(query, autoescape=True),
                func.lower(Product.brand).contains(query, autoescape=True),
                func.lower(Category.name_ru).contains(query, autoescape=True),
                func.lower(Category.name_en).contains(query, autoescape=True), ))
    if filters.category_id is not None:
        stmt = stmt.where(Product.category_id == filters.category_id)
    if filters.min_price is not None:
        stmt = stmt.where(Product.price >= filters.min_price)
    if filters.max_price is not None:
        stmt = stmt.where(Product.price <= filters.max_price)
    return stmt


def _paginate(db: Session, stmt, filters: ProductFilters) -> tuple[list[Product], int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    if filters.sort == ProductSort.POPULAR:
        sold = _units_sold_subquery()
        stmt = stmt.outerjoin(sold, sold.c.product_id == Product.id)
        order = func.coalesce(sold.c.units_sold, 0).desc()
    else:
        order = SORT_ORDER[filters.sort]

    stmt = (
        stmt.options(contains_eager(Product.category), contains_eager(Product.seller))
        .order_by(order, Product.id.desc())
        .limit(filters.limit)
        .offset(filters.offset) )
    return list(db.scalars(stmt)), total


#public
def search_products(db: Session, filters: ProductFilters) -> tuple[list[Product], int]:
    stmt = (
        select(Product)
        .join(Product.category)
        .join(Product.seller)
        .where(Product.is_active.is_(True), User.is_active.is_(True)) )
    return _paginate(db, _apply_filters(stmt, filters), filters)


def get_public_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or not product.is_available:
        raise ProductNotFoundError
    return product







#Чужой товар → 404, а не 403. Продавец не должен даже узнавать, что товар с таким ID существует
#joinedload / contains_eager загружают категорию и продавца тем же запросом. Без этого был бы N+1: для 20 товаров ещё 40 отдельных запросов
#autoescape=True экранирует % и _ в поиске, чтобы они не работали как шаблоны LIKE




#seller
def list_seller_products(db: Session, seller_id: int) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.seller_id == seller_id)
        .options(joinedload(Product.category), joinedload(Product.seller))
        .order_by(Product.created_at.desc(), Product.id.desc()) )
    return list(db.scalars(stmt))


def get_seller_product(db: Session, seller_id: int, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.seller_id != seller_id:
        raise ProductNotFoundError
    return product


def create_product(db: Session, seller: User, data: ProductCreate) -> Product:
    category_service.get_category(db, data.category_id)  # raises CategoryNotFoundError
    product = Product(seller_id=seller.id, **data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session, seller_id: int, product_id: int, data: ProductUpdate ) -> Product:
    product = get_seller_product(db, seller_id, product_id)
    updates = data.model_dump(exclude_unset=True)
    if "category_id" in updates:
        category_service.get_category(db, updates["category_id"])
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, seller_id: int, product_id: int) -> None:
    product = get_seller_product(db, seller_id, product_id)
    image = product.image
    db.delete(product)
    db.commit()
    delete_file(image)


def set_product_image(
    db: Session, seller_id: int, product_id: int, file: UploadFile ) -> Product:
    product = get_seller_product(db, seller_id, product_id)
    new_image = save_product_image(file)  # raises InvalidImageError
    old_image = product.image
    product.image = new_image
    db.commit()
    db.refresh(product)
    delete_file(old_image)
    return product