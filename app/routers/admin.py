from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import DbSession
from app.dependencies.permissions import require_admin
from app.schemas.application import ApplicationReview
from app.schemas.seller import SellerApplicationRead
from app.services import application_service
from app.services.application_service import (
    ApplicationAlreadyReviewedError, ApplicationNotFoundError, )
from app.utils.enums import ApplicationStatus

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)], )

APPLICATION_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
ALREADY_REVIEWED = HTTPException(status.HTTP_409_CONFLICT, "Application already reviewed")


@router.get("/seller-applications", response_model=list[SellerApplicationRead])
def list_seller_applications(
    db: DbSession,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None, ):
    return application_service.list_seller_applications(db, status_filter)


@router.get(
    "/seller-applications/{application_id}", response_model=SellerApplicationRead )
def get_seller_application(application_id: int, db: DbSession):
    try:
        return application_service.get_seller_application(db, application_id)
    except ApplicationNotFoundError:
        raise APPLICATION_NOT_FOUND


@router.patch(
    "/seller-applications/{application_id}", response_model=SellerApplicationRead )
def review_seller_application(
    application_id: int, data: ApplicationReview, db: DbSession ):
    try:
        return application_service.review_seller_application(db, application_id, data)
    except ApplicationNotFoundError:
        raise APPLICATION_NOT_FOUND
    except ApplicationAlreadyReviewedError:
        raise ALREADY_REVIEWED



from app.schemas.courier import CourierApplicationRead

@router.get("/courier-applications", response_model=list[CourierApplicationRead])
def list_courier_applications(
    db: DbSession,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None, ):
    return application_service.list_courier_applications(db, status_filter)


@router.get(
    "/courier-applications/{application_id}", response_model=CourierApplicationRead )
def get_courier_application(application_id: int, db: DbSession):
    try:
        return application_service.get_courier_application(db, application_id)
    except ApplicationNotFoundError:
        raise APPLICATION_NOT_FOUND


@router.patch(
    "/courier-applications/{application_id}", response_model=CourierApplicationRead )
def review_courier_application(
    application_id: int, data: ApplicationReview, db: DbSession ):
    try:
        return application_service.review_courier_application(db, application_id, data)
    except ApplicationNotFoundError:
        raise APPLICATION_NOT_FOUND
    except ApplicationAlreadyReviewedError:
        raise ALREADY_REVIEWED



from app.schemas.order import OrderRead, OrderStatusUpdate
from app.services import order_service
from app.services.order_service import (
    DeliveryManagedByCourierError, InvalidStatusTransitionError, OrderNotFoundError, )
from app.utils.enums import OrderStatus

ORDER_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")


@router.get("/orders", response_model=list[OrderRead])
def list_orders(
    db: DbSession,
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None, ):
    return order_service.list_all_orders(db, status_filter)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: DbSession):
    try:
        return order_service.get_order(db, order_id)
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND


@router.patch("/orders/{order_id}", response_model=OrderRead)
def update_order_status(order_id: int, data: OrderStatusUpdate, db: DbSession):
    try:
        return order_service.update_order_status(db, order_id, data.status)
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND
    except InvalidStatusTransitionError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))
    except DeliveryManagedByCourierError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Delivery is managed by the assigned courier")




from app.schemas.delivery import CourierAssign, CourierInfo
from app.services import delivery_service
from app.services.delivery_service import (
    CourierNotFoundError,
    DeliveryAlreadyStartedError,
    OrderNotAssignableError, )


@router.get("/couriers", response_model=list[CourierInfo])
def list_couriers(db: DbSession):
    return [CourierInfo.from_model(c) for c in delivery_service.list_couriers(db)]


@router.post("/orders/{order_id}/assign-courier", response_model=OrderRead)
def assign_courier(order_id: int, data: CourierAssign, db: DbSession):
    try:
        return delivery_service.assign_courier(db, order_id, data.courier_id)
    except OrderNotFoundError:
        raise ORDER_NOT_FOUND
    except CourierNotFoundError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Courier not found or inactive")
    except OrderNotAssignableError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Courier can only be assigned to confirmed or processing orders", )
    except DeliveryAlreadyStartedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Delivery has already started")