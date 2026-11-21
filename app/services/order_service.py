from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services import cart_service
from app.utils.enums import OrderStatus


class EmptyCartError(Exception):
    pass


class ProductUnavailableError(Exception):
    def __init__(self, product_name: str):
        self.product_name = product_name
        super().__init__(f"Product '{product_name}' is no longer available")


class OutOfStockError(Exception):
    def __init__(self, product_name: str):
        self.product_name = product_name
        super().__init__(f"Not enough stock for '{product_name}'")


class OrderNotFoundError(Exception):
    pass


#checkout
def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    cart = cart_service.get_or_create_cart(db, user.id)
    if not cart.items:
        raise EmptyCartError

    order = Order(user_id=user.id, **data.model_dump())
    total = Decimal("0")

    try:
        for cart_item in cart.items:
            product = cart_item.product
            if not product.is_active or product.seller_id == user.id:
                raise ProductUnavailableError(product.name)

            # Атомарно: проверка остатка и списание одной операцией
            result = db.execute(
                update(Product)
                .where(
                    Product.id == product.id,
                    Product.is_active.is_(True),
                    Product.quantity >= cart_item.quantity, )
                .values(quantity=Product.quantity - cart_item.quantity) )
            if result.rowcount != 1:
                raise OutOfStockError(product.name)

            # Снимок товара на момент покупки
            order.items.append(
                OrderItem(
                    product_id=product.id,
                    seller_id=product.seller_id,
                    product_name=product.name,
                    price=product.price,
                    quantity=cart_item.quantity, ) )
            total += product.price * cart_item.quantity

        order.total_price = total
        db.add(order)
        cart.items.clear()
        db.commit()
    
    except Exception:
        db.rollback()
        raise

    db.refresh(order)
    return order




class InvalidStatusTransitionError(Exception):
    def __init__(self, current: OrderStatus, new: OrderStatus):
        super().__init__(f"Cannot change status from '{current.value}' to '{new.value}'")


class OrderNotCancellableError(Exception):
    pass


class DeliveryManagedByCourierError(Exception):
    pass


# Once a courier is assigned, only the courier moves the order to these statuses
COURIER_MANAGED_STATUSES = {OrderStatus.SHIPPED, OrderStatus.DELIVERED}


ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(), }


def _restock(db: Session, order: Order) -> None:
    for item in order.items:
        if item.product_id is not None:  # товар могли удалить
            db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(quantity=Product.quantity + item.quantity) )


def apply_status_change(
    db: Session, order: Order, new_status: OrderStatus, *, by_courier: bool = False ) -> None:
    """Validate and apply a status transition without committing.

    Callers (e.g. delivery_service) combine it with other changes
    and commit everything in a single transaction.
    """
    if new_status not in ALLOWED_TRANSITIONS[order.status]:
        raise InvalidStatusTransitionError(order.status, new_status)
    if order.courier_id is not None and new_status in COURIER_MANAGED_STATUSES and not by_courier:
        raise DeliveryManagedByCourierError
    if new_status == OrderStatus.CANCELLED:
        _restock(db, order)
        # Only possible before pickup (shipped orders cannot be cancelled):
        # release the courier so the order leaves their delivery list
        order.courier_id = None
        order.delivery_status = None
        order.assigned_at = None
    order.status = new_status


def _change_status(db: Session, order: Order, new_status: OrderStatus) -> Order:
    try:
        apply_status_change(db, order, new_status)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return order


#customer
def list_user_orders(db: Session, user_id: int) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc()) )
    return list(db.scalars(stmt))


def get_user_order(db: Session, user_id: int, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user_id:
        raise OrderNotFoundError
    return order


def cancel_user_order(db: Session, user_id: int, order_id: int) -> Order:
    order = get_user_order(db, user_id, order_id)
    if order.status != OrderStatus.PENDING:
        raise OrderNotCancellableError  # покупатель может отменить только до подтверждения
    return _change_status(db, order, OrderStatus.CANCELLED)


#admin
def list_all_orders(db: Session, status: OrderStatus | None = None) -> list[Order]:
    stmt = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
    if status is not None:
        stmt = stmt.where(Order.status == status)
    return list(db.scalars(stmt))


def get_order(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise OrderNotFoundError
    return order


def update_order_status(db: Session, order_id: int, new_status: OrderStatus) -> Order:
    return _change_status(db, get_order(db, order_id), new_status)


#seller
def list_seller_orders(
    db: Session, seller_id: int ) -> list[tuple[Order, list[OrderItem]]]:
    items = db.scalars(
        select(OrderItem)
        .where(OrderItem.seller_id == seller_id)
        .options(joinedload(OrderItem.order))
        .order_by(OrderItem.order_id.desc(), OrderItem.id)   )
    grouped: dict[int, list[OrderItem]] = {}
    for item in items:
        grouped.setdefault(item.order_id, []).append(item)
    return [(order_items[0].order, order_items) for order_items in grouped.values()]