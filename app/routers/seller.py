from fastapi import APIRouter, HTTPException, UploadFile, status
from app.database import DbSession
from app.dependencies.language import CurrentLanguage
from app.dependencies.permissions import SellerUser
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service
from app.services.category_service import CategoryNotFoundError
from app.services.product_service import ProductNotFoundError
from app.utils.files import InvalidImageError

router = APIRouter(prefix="/seller", tags=["Seller"])

PRODUCT_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
CATEGORY_NOT_FOUND = HTTPException(status.HTTP_400_BAD_REQUEST, "Category does not exist")


@router.get("/products", response_model=list[ProductRead])
def list_my_products(seller: SellerUser, db: DbSession, lang: CurrentLanguage):
    products = product_service.list_seller_products(db, seller.id)
    return [ProductRead.from_model(p, lang) for p in products]


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate, seller: SellerUser, db: DbSession, lang: CurrentLanguage ):
    try:
        product = product_service.create_product(db, seller, data)
    except CategoryNotFoundError:
        raise CATEGORY_NOT_FOUND
    return ProductRead.from_model(product, lang)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_my_product(
    product_id: int, seller: SellerUser, db: DbSession, lang: CurrentLanguage ):
    try:
        product = product_service.get_seller_product(db, seller.id, product_id)
    except ProductNotFoundError:
        raise PRODUCT_NOT_FOUND
    return ProductRead.from_model(product, lang)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    data: ProductUpdate,
    seller: SellerUser,
    db: DbSession,
    lang: CurrentLanguage, ):
    try:
        product = product_service.update_product(db, seller.id, product_id, data)
    except ProductNotFoundError:
        raise PRODUCT_NOT_FOUND
    except CategoryNotFoundError:
        raise CATEGORY_NOT_FOUND
    return ProductRead.from_model(product, lang)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, seller: SellerUser, db: DbSession):
    try:
        product_service.delete_product(db, seller.id, product_id)
    except ProductNotFoundError:
        raise PRODUCT_NOT_FOUND


@router.post("/products/{product_id}/image", response_model=ProductRead)
def upload_product_image(
    product_id: int,
    file: UploadFile,
    seller: SellerUser,
    db: DbSession,
    lang: CurrentLanguage, ):
    try:
        product = product_service.set_product_image(db, seller.id, product_id, file)
    except ProductNotFoundError:
        raise PRODUCT_NOT_FOUND
    except InvalidImageError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
    return ProductRead.from_model(product, lang)


from app.dependencies.auth import CurrentUser
from app.schemas.seller import SellerApplicationCreate, SellerApplicationRead
from app.services import application_service
from app.services.application_service import (
    ApplicationAlreadyPendingError,  ApplicationNotFoundError,  RoleAlreadyGrantedError, )


@router.post(
    "/applications",
    response_model=SellerApplicationRead,
    status_code=status.HTTP_201_CREATED, )
def submit_application(data: SellerApplicationCreate, user: CurrentUser, db: DbSession):
    try:
        return application_service.submit_seller_application(db, user, data)
    except RoleAlreadyGrantedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already a seller")
    except ApplicationAlreadyPendingError:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have a pending application")
    except CategoryNotFoundError:
        raise CATEGORY_NOT_FOUND


@router.get("/applications/me", response_model=SellerApplicationRead)
def get_my_application(user: CurrentUser, db: DbSession):
    try:
        return application_service.get_latest_seller_application(db, user.id)
    except ApplicationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No application found")


    from app.schemas.seller import SellerProfileRead, SellerProfileUpdate
from app.services.application_service import SellerProfileNotFoundError

STORE_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Store profile not found")


@router.get("/store", response_model = SellerProfileRead)
def get_my_store(seller: SellerUser):
    try:
        return application_service.get_seller_profile(seller)
    except SellerProfileNotFoundError:
        raise STORE_NOT_FOUND


@router.patch("/store", response_model=SellerProfileRead)
def update_my_store(data: SellerProfileUpdate, seller: SellerUser, db: DbSession):
    try:
        return application_service.update_seller_profile(db, seller, data)
    except SellerProfileNotFoundError:
        raise STORE_NOT_FOUND


from app.schemas.order import SellerOrderRead
from app.services import order_service


@router.get("/orders", response_model=list[SellerOrderRead])
def list_my_orders(seller: SellerUser, db: DbSession):
    return [
        SellerOrderRead.from_items(order, items)
        for order, items in order_service.list_seller_orders(db, seller.id) ]