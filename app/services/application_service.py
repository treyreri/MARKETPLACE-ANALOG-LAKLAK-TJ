from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.seller_application import SellerApplication
from app.models.seller_profile import SellerProfile
from app.models.user import User, UserRole
from app.schemas.application import ApplicationReview
from app.schemas.seller import SellerApplicationCreate, SellerProfileUpdate
from app.services import category_service
from app.utils.enums import ApplicationStatus, RoleName


class ApplicationNotFoundError(Exception):
    pass


class ApplicationAlreadyPendingError(Exception):
    pass


class ApplicationAlreadyReviewedError(Exception):
    pass


class RoleAlreadyGrantedError(Exception):
    pass


class SellerProfileNotFoundError(Exception):
    pass


#seller application : user side
def submit_seller_application(
    db: Session, user: User, data: SellerApplicationCreate ) -> SellerApplication:
    if user.has_role(RoleName.SELLER):
        raise RoleAlreadyGrantedError

    pending = db.scalar(
        select(SellerApplication.id).where(
            SellerApplication.user_id == user.id,
            SellerApplication.status == ApplicationStatus.PENDING, ) )
    if pending is not None:
        raise ApplicationAlreadyPendingError

    if data.category_id is not None:
        category_service.get_category(db, data.category_id)

    application = SellerApplication(user_id=user.id, **data.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_latest_seller_application(db: Session, user_id: int) -> SellerApplication:
    application = db.scalar(
        select(SellerApplication)
        .where(SellerApplication.user_id == user_id)
        .order_by(SellerApplication.created_at.desc(), SellerApplication.id.desc())
        .limit(1) )
    if application is None:
        raise ApplicationNotFoundError
    return application


#seller application : admin side
def list_seller_applications(
    db: Session, status: ApplicationStatus | None = None ) -> list[SellerApplication]:
    stmt = select(SellerApplication).order_by(SellerApplication.created_at.desc())
    if status is not None:
        stmt = stmt.where(SellerApplication.status == status)
    return list(db.scalars(stmt))


def get_seller_application(db: Session, application_id: int) -> SellerApplication:
    application = db.get(SellerApplication, application_id)
    if application is None:
        raise ApplicationNotFoundError
    return application


def review_seller_application(
    db: Session, application_id: int, data: ApplicationReview ) -> SellerApplication:
    application = get_seller_application(db, application_id)
    if application.status != ApplicationStatus.PENDING:
        raise ApplicationAlreadyReviewedError

    application.status = data.status
    application.admin_comment = data.admin_comment
    application.reviewed_at = datetime.now(timezone.utc)

    if data.status == ApplicationStatus.APPROVED:
        _activate_seller(application)

    db.commit()  # статус, роль и магазин сохраняются одной транзакцией
    db.refresh(application)
    return application


def _activate_seller(application: SellerApplication) -> None:
    user = application.user
    if not user.has_role(RoleName.SELLER):
        user.roles.append(UserRole(role=RoleName.SELLER))

    store_data = {
        "store_name": application.store_name,
        "store_description": application.store_description,
        "address": application.address,
        "phone_number": application.phone_number,  }
    if user.seller_profile is None:
        user.seller_profile = SellerProfile(**store_data)
    else:
        for field, value in store_data.items():
            setattr(user.seller_profile, field, value)


#seller profile(store )
def get_seller_profile(user: User) -> SellerProfile:
    if user.seller_profile is None:
        raise SellerProfileNotFoundError
    return user.seller_profile


def update_seller_profile(
    db: Session, user: User, data: SellerProfileUpdate ) -> SellerProfile:
    profile = get_seller_profile(user)
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile

