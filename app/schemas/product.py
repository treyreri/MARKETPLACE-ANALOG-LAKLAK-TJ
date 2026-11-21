from datetime import datetime
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, model_validator
from app.models.product import Product
from app.utils.enums import Language, ProductSort

Price = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    price: Price
    quantity: int = Field(ge=0)
    category_id: int


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    price: Price | None = None
    quantity: int | None = Field(default=None, ge=0)
    category_id: int | None = None


class ProductFilters(BaseModel):
    q: str | None = Field(default=None, max_length=100)
    category_id: int | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    sort: ProductSort = ProductSort.NEWEST
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_price_range(self):
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price ):
            raise ValueError("min_price cannot be greater than max_price")
        return self


class CategoryShort(BaseModel):
    id: int
    name: str


class SellerShort(BaseModel):
    id: int
    name: str


class ProductRead(BaseModel):
    id: int
    name: str
    description: str | None
    brand: str | None
    price: Decimal
    quantity: int
    image_url: str | None
    is_active: bool
    created_at: datetime
    category: CategoryShort
    seller: SellerShort

    @classmethod
    def from_model(cls, product: Product, lang: Language) -> "ProductRead":
        return cls(
            id=product.id,
            name=product.name,
            description=product.description,
            brand=product.brand,
            price=product.price,
            quantity=product.quantity,
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            category=CategoryShort(
                id=product.category.id, name=product.category.get_name(lang) ),
            seller=SellerShort(id=product.seller.id, name=product.seller.display_name), )


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int
    limit: int
    offset: int



#ProductFilters собирает все параметры поиска в одну модель. FastAPI умеет принимать такую 
# модель из query-параметров,
# и валидация (например, min_price > max_price) живёт в одном месте

#ProductList содержит total. Он понадобится frontend'у для пагинации

#Decimal в JSON приходит строкой ("250.00"). 
# так задумано: цена не теряет точность, как это бывает с float