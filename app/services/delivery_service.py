from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.order import Order
from app.models.user import User, UserRole
from app.services import order_service
from app.services.order_service import OrderNotFoundError
from app.utils.enums import DeliveryStatus, OrderStatus, RoleName


class CourierNotFoundError(Exception):
    pass


class OrderNotAssignableError(Exception):
    pass


class DeliveryAlreadyStartedError(Exception):
    pass


class InvalidDeliveryTransitionError(Exception):
    def __init__(self, current: DeliveryStatus, new: DeliveryStatus):
        super().__init__(
            f"Cannot change delivery status from '{current.value}' to '{new.value}'" )


ASSIGNABLE_ORDER_STATUSES = {OrderStatus.CONFIRMED, OrderStatus.PROCESSING}

# Доставка двигается строго по шагам: следующий статус ровно один
NEXT_DELIVERY_STATUS = {
    DeliveryStatus.ASSIGNED: DeliveryStatus.PICKED_UP,
    DeliveryStatus.PICKED_UP: DeliveryStatus.IN_DELIVERY,
    DeliveryStatus.IN_DELIVERY: DeliveryStatus.DELIVERED, }

# Какие шаги доставки меняют статус заказа
ORDER_STATUS_FOR_DELIVERY = {
    DeliveryStatus.PICKED_UP: OrderStatus.SHIPPED,
    DeliveryStatus.DELIVERED: OrderStatus.DELIVERED, }


#admin
def list_couriers(db: Session) -> list[User]:
    stmt = (
        select(User)
        .join(User.roles)
        .where(UserRole.role == RoleName.COURIER, User.is_active.is_(True))
        .options(selectinload(User.courier_profile))
        .order_by(User.id)  )
    return list(db.scalars(stmt))


def _get_active_courier(db: Session, courier_id: int) -> User:
    user = db.get(User, courier_id)
    if user is None or not user.is_active or not user.has_role(RoleName.COURIER):
        raise CourierNotFoundError
    return user


def assign_courier(db: Session, order_id: int, courier_id: int) -> Order:
    order = order_service.get_order(db, order_id)
    if order.status not in ASSIGNABLE_ORDER_STATUSES:
        raise OrderNotAssignableError
    if order.delivery_status not in (None, DeliveryStatus.ASSIGNED):
        raise DeliveryAlreadyStartedError
    courier = _get_active_courier(db, courier_id)

    try:
        if order.status == OrderStatus.CONFIRMED:
            order_service.apply_status_change(db, order, OrderStatus.PROCESSING)
        order.courier_id = courier.id
        order.delivery_status = DeliveryStatus.ASSIGNED
        order.assigned_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return order


#courier
def list_courier_orders(db: Session, courier_id: int, active_only: bool = True) -> list[Order]:
    stmt = select(Order).where(Order.courier_id == courier_id)
    if active_only:
        stmt = stmt.where(Order.delivery_status != DeliveryStatus.DELIVERED)
    stmt = stmt.order_by(Order.assigned_at.desc(), Order.id.desc())
    return list(db.scalars(stmt))


def get_courier_order(db: Session, courier_id: int, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.courier_id != courier_id:
        raise OrderNotFoundError
    return order


def update_delivery_status(
    db: Session, courier_id: int, order_id: int, new_status: DeliveryStatus ) -> Order:
    order = get_courier_order(db, courier_id, order_id)
    if NEXT_DELIVERY_STATUS.get(order.delivery_status) != new_status:
        raise InvalidDeliveryTransitionError(order.delivery_status, new_status)

    try:
        order.delivery_status = new_status
        if new_status in ORDER_STATUS_FOR_DELIVERY:
            order_service.apply_status_change(
                db, order, ORDER_STATUS_FOR_DELIVERY[new_status], by_courier=True )
        if new_status == DeliveryStatus.DELIVERED:
            order.delivered_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return order