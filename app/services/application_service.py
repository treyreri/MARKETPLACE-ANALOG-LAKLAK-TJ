from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.courier_application import CourierApplication
from app.models.courier_profile import CourierProfile
from app.models.seller_application import SellerApplication
from app.models.seller_profile import SellerProfile
from app.models.user import User, UserRole
from app.schemas.application import ApplicationReview
from app.schemas.courier import CourierApplicationCreate, CourierProfileUpdate
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


#shared helpers (work with any application model)
def _save(db: Session, obj):
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _ensure_can_apply(db: Session, model, user: User, role: RoleName) -> None:
    if user.has_role(role):
        raise RoleAlreadyGrantedError
    pending = db.scalar(
        select(model.id).where(
            model.user_id == user.id,
            model.status == ApplicationStatus.PENDING, ))
    if pending is not None:
        raise ApplicationAlreadyPendingError


def _get_latest(db: Session, model, user_id: int):
    application = db.scalar(
        select(model)
        .where(model.user_id == user_id)
        .order_by(model.created_at.desc(), model.id.desc())
        .limit(1) )
    if application is None:
        raise ApplicationNotFoundError
    return application


def _list(db: Session, model, status: ApplicationStatus | None):
    stmt = select(model).order_by(model.created_at.desc(), model.id.desc())
    if status is not None:
        stmt = stmt.where(model.status == status)
    return list(db.scalars(stmt))


def _get(db: Session, model, application_id: int):
    application = db.get(model, application_id)
    if application is None:
        raise ApplicationNotFoundError
    return application


def _apply_review(application, data: ApplicationReview) -> None:
    if application.status != ApplicationStatus.PENDING:
        raise ApplicationAlreadyReviewedError
    application.status = data.status
    application.admin_comment = data.admin_comment
    application.reviewed_at = datetime.now(timezone.utc)


def _grant_role(user: User, role: RoleName) -> None:
    if not user.has_role(role):
        user.roles.append(UserRole(role=role))


def _update_fields(obj, values: dict) -> None:
    for field, value in values.items():
        setattr(obj, field, value)


#seller
def submit_seller_application(
    db: Session, user: User, data: SellerApplicationCreate ) -> SellerApplication:
    _ensure_can_apply(db, SellerApplication, user, RoleName.SELLER)
    if data.category_id is not None:
        category_service.get_category(db, data.category_id)
    return _save(db, SellerApplication(user_id=user.id, **data.model_dump()))


def get_latest_seller_application(db: Session, user_id: int) -> SellerApplication:
    return _get_latest(db, SellerApplication, user_id)


def list_seller_applications(
    db: Session, status: ApplicationStatus | None = None ) -> list[SellerApplication]:
    return _list(db, SellerApplication, status)


def get_seller_application(db: Session, application_id: int) -> SellerApplication:
    return _get(db, SellerApplication, application_id)


def review_seller_application(
    db: Session, application_id: int, data: ApplicationReview ) -> SellerApplication:
    application = _get(db, SellerApplication, application_id)
    _apply_review(application, data)
    if data.status == ApplicationStatus.APPROVED:
        _activate_seller(application)
    db.commit()  # статус, роль и магазин сохраняются одной транзакцией
    db.refresh(application)
    return application


def _activate_seller(application: SellerApplication) -> None:
    user = application.user
    _grant_role(user, RoleName.SELLER)
    store_data = {
        "store_name": application.store_name,
        "store_description": application.store_description,
        "address": application.address,
        "phone_number": application.phone_number, }
    if user.seller_profile is None:
        user.seller_profile = SellerProfile(**store_data)
    else:
        _update_fields(user.seller_profile, store_data)


def get_seller_profile(user: User) -> SellerProfile:
    if user.seller_profile is None:
        raise SellerProfileNotFoundError
    return user.seller_profile


def update_seller_profile(
    db: Session, user: User, data: SellerProfileUpdate ) -> SellerProfile:
    profile = get_seller_profile(user)
    _update_fields(profile, data.model_dump(exclude_unset=True, exclude_none=True))
    db.commit()
    db.refresh(profile)
    return profile



class CourierProfileNotFoundError(Exception):
    pass

#courier
def submit_courier_application(
    db: Session, user: User, data: CourierApplicationCreate ) -> CourierApplication:
    _ensure_can_apply(db, CourierApplication, user, RoleName.COURIER)
    return _save(db, CourierApplication(user_id=user.id, **data.model_dump()))


def get_latest_courier_application(db: Session, user_id: int) -> CourierApplication:
    return _get_latest(db, CourierApplication, user_id)


def list_courier_applications(
    db: Session, status: ApplicationStatus | None = None ) -> list[CourierApplication]:
    return _list(db, CourierApplication, status)


def get_courier_application(db: Session, application_id: int) -> CourierApplication:
    return _get(db, CourierApplication, application_id)


def review_courier_application(
    db: Session, application_id: int, data: ApplicationReview ) -> CourierApplication:
    application = _get(db, CourierApplication, application_id)
    _apply_review(application, data)
    if data.status == ApplicationStatus.APPROVED:
        _activate_courier(application)
    db.commit()
    db.refresh(application)
    return application


def _activate_courier(application: CourierApplication) -> None:
    user = application.user
    _grant_role(user, RoleName.COURIER)
    profile_data = {
        "phone_number": application.phone_number,
        "address": application.address,
        "transport_type": application.transport_type,  }
    if user.courier_profile is None:
        user.courier_profile = CourierProfile(**profile_data)
    else:
        _update_fields(user.courier_profile, profile_data)


def get_courier_profile(user: User) -> CourierProfile:
    if user.courier_profile is None:
        raise CourierProfileNotFoundError
    return user.courier_profile


def update_courier_profile(
    db: Session, user: User, data: CourierProfileUpdate ) -> CourierProfile:
    profile = get_courier_profile(user)
    _update_fields(profile, data.model_dump(exclude_unset=True, exclude_none=True))
    db.commit()
    db.refresh(profile)
    return profile