from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemAdd, CartItemUpdate


class CartItemNotFoundError(Exception):
    pass


class ProductUnavailableError(Exception):
    pass


class OwnProductError(Exception):
    pass


class InsufficientStockError(Exception):
    def __init__(self, available: int):
        self.available = available
        super().__init__(f"Only {available} items available")


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    stmt = select(Cart).where(Cart.user_id == user_id)
    cart = db.scalar(stmt)
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        try:
            db.commit()
        except IntegrityError:
            # A concurrent request created the cart first: use that one
            db.rollback()
            return db.execute(stmt).scalar_one()
        db.refresh(cart)
    return cart


def _get_purchasable_product(db: Session, product_id: int, user_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise ProductUnavailableError
    if product.seller_id == user_id:
        raise OwnProductError
    return product


def _ensure_in_stock(product: Product, quantity: int) -> None:
    if quantity > product.quantity:
        raise InsufficientStockError(product.quantity)


def _find_item(cart: Cart, item_id: int) -> CartItem:
    for item in cart.items:
        if item.id == item_id:
            return item
    raise CartItemNotFoundError


def _save_cart(db: Session, cart: Cart) -> Cart:
    db.commit()
    db.refresh(cart)
    return cart


def add_item(db: Session, user_id: int, data: CartItemAdd) -> Cart:
    cart = get_or_create_cart(db, user_id)
    product = _get_purchasable_product(db, data.product_id, user_id)

    existing = next((i for i in cart.items if i.product_id == product.id), None)
    new_quantity = data.quantity + (existing.quantity if existing else 0)
    _ensure_in_stock(product, new_quantity)

    if existing:
        existing.quantity = new_quantity
    else:
        cart.items.append(CartItem(product=product, quantity=new_quantity))
    return _save_cart(db, cart)


def update_item(db: Session, user_id: int, item_id: int, data: CartItemUpdate) -> Cart:
    cart = get_or_create_cart(db, user_id)
    item = _find_item(cart, item_id)
    if not item.product.is_active:
        raise ProductUnavailableError
    _ensure_in_stock(item.product, data.quantity)
    item.quantity = data.quantity
    return _save_cart(db, cart)


def remove_item(db: Session, user_id: int, item_id: int) -> Cart:
    cart = get_or_create_cart(db, user_id)
    cart.items.remove(_find_item(cart, item_id))  # delete-orphan удалит строку
    return _save_cart(db, cart)


def clear_cart(db: Session, user_id: int) -> Cart:
    cart = get_or_create_cart(db, user_id)
    cart.items.clear()
    return _save_cart(db, cart)