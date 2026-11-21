from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from app.database import DbSession
from app.dependencies.language import CurrentLanguage
from app.models.product import Product
from app.schemas.product import ProductFilters, ProductList, ProductRead
from app.services import product_service
from app.utils.enums import Language

router = APIRouter(prefix="/products", tags=["Products"])
Filters = Annotated[ProductFilters, Query()]


def _to_list(
    items: list[Product], total: int, filters: ProductFilters, lang: Language ) -> ProductList:
    return ProductList(
        items=[ProductRead.from_model(p, lang) for p in items],
        total=total, limit=filters.limit, offset=filters.offset, )


@router.get("", response_model=ProductList)
def list_products(filters: Filters, db: DbSession, lang: CurrentLanguage):
    items, total = product_service.search_products(db, filters)
    return _to_list(items, total, filters, lang)


@router.get("/search", response_model=ProductList)
def search_products(filters: Filters, db: DbSession, lang: CurrentLanguage):
    items, total = product_service.search_products(db, filters)
    return _to_list(items, total, filters, lang)


@router.get("/category/{category_id}", response_model=ProductList)
def list_products_by_category(
    category_id: int, filters: Filters, db: DbSession, lang: CurrentLanguage ):
    filters = filters.model_copy(update={"category_id": category_id})
    items, total = product_service.search_products(db, filters)
    return _to_list(items, total, filters, lang)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: DbSession, lang: CurrentLanguage):
    try:
        return ProductRead.from_model(
            product_service.get_public_product(db, product_id), lang )
    except product_service.ProductNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")