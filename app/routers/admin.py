from fastapi import APIRouter, Depends, HTTPException, status

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
def list_seller_applications(db: DbSession, status: ApplicationStatus | None = None):
    return application_service.list_seller_applications(db, status)


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