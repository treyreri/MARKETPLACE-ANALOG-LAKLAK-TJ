from fastapi import APIRouter, HTTPException, status

from app.database import DbSession
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import CourierUser
from app.schemas.courier import (
    CourierApplicationCreate,
    CourierApplicationRead,
    CourierProfileRead,
    CourierProfileUpdate, )
from app.services import application_service
from app.services.application_service import (
    ApplicationAlreadyPendingError,
    ApplicationNotFoundError,
    CourierProfileNotFoundError,
    RoleAlreadyGrantedError, )

router = APIRouter(prefix="/courier", tags=["Courier"])
PROFILE_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Courier profile not found")


@router.post(
    "/applications",
    response_model=CourierApplicationRead,
    status_code=status.HTTP_201_CREATED, )
def submit_application(data: CourierApplicationCreate, user: CurrentUser, db: DbSession):
    try:
        return application_service.submit_courier_application(db, user, data)
    except RoleAlreadyGrantedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already a courier")
    except ApplicationAlreadyPendingError:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have a pending application")


@router.get("/applications/me", response_model=CourierApplicationRead)
def get_my_application(user: CurrentUser, db: DbSession):
    try:
        return application_service.get_latest_courier_application(db, user.id)
    except ApplicationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No application found")


@router.get("/profile", response_model=CourierProfileRead)
def get_my_profile(courier: CourierUser):
    try:
        return application_service.get_courier_profile(courier)
    except CourierProfileNotFoundError:
        raise PROFILE_NOT_FOUND


@router.patch("/profile", response_model=CourierProfileRead)
def update_my_profile(data: CourierProfileUpdate, courier: CourierUser, db: DbSession):
    try:
        return application_service.update_courier_profile(db, courier, data)
    except CourierProfileNotFoundError:
        raise PROFILE_NOT_FOUND



from app.schemas.delivery import CourierOrderRead, DeliveryStatusUpdate
from app.services import delivery_service
from app.services.delivery_service import InvalidDeliveryTransitionError
from app.services.order_service import InvalidStatusTransitionError, OrderNotFoundError

ORDER_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")


@router.get("/orders", response_model=list[CourierOrderRead])
def list_my_deliveries(courier: CourierUser, db: DbSession, active_only: bool = True):
    return delivery_service.list_courier_orders(db, courier.id, active_only)


@router.get("/orders/{order_id}", response_model=CourierOrderRead)
def get_my_delivery(order_id: int, courier: CourierUser, db: DbSession):
    try:
        return delivery_service.get_courier_order(db, courier.id, order_id)
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND


@router.patch("/orders/{order_id}/status", response_model=CourierOrderRead)
def update_delivery_status(
    order_id: int, data: DeliveryStatusUpdate, courier: CourierUser, db: DbSession ):
    try:
        return delivery_service.update_delivery_status(
            db, courier.id, order_id, data.status )
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND
    except (InvalidDeliveryTransitionError, InvalidStatusTransitionError) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))