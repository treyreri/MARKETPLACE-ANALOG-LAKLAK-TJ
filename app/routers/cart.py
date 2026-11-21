from fastapi import APIRouter, HTTPException, status
from app.database import DbSession
from app.dependencies.auth import CurrentUser
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartRead
from app.services import cart_service
from app.services.cart_service import (
    CartItemNotFoundError,
    InsufficientStockError,  OwnProductError, ProductUnavailableError, )

router = APIRouter(prefix="/cart", tags=["Cart"])


def _handle_cart_errors(error: Exception) -> HTTPException:
    if isinstance(error, CartItemNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found")
    if isinstance(error, ProductUnavailableError):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Product not found or unavailable")
    if isinstance(error, OwnProductError):
        return HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot buy your own product")
    if isinstance(error, InsufficientStockError):
        return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
    raise error


CART_ERRORS = (
    CartItemNotFoundError,
    ProductUnavailableError,
    OwnProductError,
    InsufficientStockError, )


@router.get("", response_model=CartRead)
def get_cart(user: CurrentUser, db: DbSession):
    return CartRead.from_model(cart_service.get_or_create_cart(db, user.id))


@router.post("/items", response_model=CartRead)
def add_item(data: CartItemAdd, user: CurrentUser, db: DbSession):
    try:
        return CartRead.from_model(cart_service.add_item(db, user.id, data))
    except CART_ERRORS as error:
        raise _handle_cart_errors(error)


@router.patch("/items/{item_id}", response_model=CartRead)
def update_item(item_id: int, data: CartItemUpdate, user: CurrentUser, db: DbSession):
    try:
        return CartRead.from_model(cart_service.update_item(db, user.id, item_id, data))
    except CART_ERRORS as error:
        raise _handle_cart_errors(error)


@router.delete("/items/{item_id}", response_model=CartRead)
def remove_item(item_id: int, user: CurrentUser, db: DbSession):
    try:
        return CartRead.from_model(cart_service.remove_item(db, user.id, item_id))
    except CART_ERRORS as error:
        raise _handle_cart_errors(error)


@router.delete("", response_model=CartRead)
def clear_cart(user: CurrentUser, db: DbSession):
    return CartRead.from_model(cart_service.clear_cart(db, user.id))