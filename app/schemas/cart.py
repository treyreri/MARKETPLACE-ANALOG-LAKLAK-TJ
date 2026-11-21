from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.cart import Cart, CartItem


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartProduct(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url: str | None
    available_quantity: int
    is_active: bool


class CartItemRead(BaseModel):
    id: int
    quantity: int
    line_total: Decimal
    is_valid: bool
    product: CartProduct

    @classmethod
    def from_model(cls, item: CartItem) -> "CartItemRead":
        product = item.product
        return cls(
            id=item.id,
            quantity=item.quantity,
            line_total=item.line_total,
            is_valid=item.is_valid,
            product=CartProduct(
                id=product.id,
                name=product.name,
                price=product.price,
                image_url=product.image_url,
                available_quantity=product.quantity,
                is_active=product.is_active, ), )


class CartRead(BaseModel):
    id: int
    items: list[CartItemRead]
    total_quantity: int
    total_price: Decimal
    can_checkout: bool

    @classmethod
    def from_model(cls, cart: Cart) -> "CartRead":
        return cls(
            id=cart.id,
            items=[CartItemRead.from_model(item) for item in cart.items],
            total_quantity=cart.total_quantity,
            total_price=cart.total_price,
            can_checkout=cart.can_checkout, )