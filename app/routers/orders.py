from fastapi import APIRouter, HTTPException, status
from app.database import DbSession
from app.dependencies.auth import CurrentUser
from app.schemas.order import OrderCreate, OrderRead
from app.services import order_service
from app.services.order_service import (
    EmptyCartError,
    OrderNotCancellableError, OrderNotFoundError, OutOfStockError,  ProductUnavailableError, )

router = APIRouter(prefix="/orders", tags=["Orders"])
ORDER_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, user: CurrentUser, db: DbSession):
    try:
        return order_service.create_order(db, user, data)
    except EmptyCartError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cart is empty")
    except (ProductUnavailableError, OutOfStockError) as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))


@router.get("", response_model=list[OrderRead])
def list_my_orders(user: CurrentUser, db: DbSession):
    return order_service.list_user_orders(db, user.id)


@router.get("/{order_id}", response_model=OrderRead)
def get_my_order(order_id: int, user: CurrentUser, db: DbSession):
    try:
        return order_service.get_user_order(db, user.id, order_id)
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_my_order(order_id: int, user: CurrentUser, db: DbSession):
    try:
        return order_service.cancel_user_order(db, user.id, order_id)
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND
    except OrderNotCancellableError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only pending orders can be cancelled" )