"""Demo data for local development.

Run:  python -m app.scripts.seed_demo_data

Idempotent: users are matched by demo phone number, products by seller + name,
and orders are created only if the demo customer has none yet.
Everything goes through the regular services, so business rules apply
(stock checks, snapshots, status transitions). Demo passwords are for local
development only.
"""
import io
import random
from decimal import Decimal

from fastapi import UploadFile
from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.database import SessionLocal
from app.models import Category, Order, Product, User, UserRole
from app.schemas.application import ApplicationReview
from app.schemas.cart import CartItemAdd
from app.schemas.courier import CourierApplicationCreate
from app.schemas.order import OrderCreate
from app.schemas.product import ProductCreate
from app.schemas.seller import SellerApplicationCreate
from app.schemas.user import UserRegister
from app.scripts.seed_categories import seed_categories
from app.services import (
    application_service, auth_service, cart_service, delivery_service, order_service,
    product_service, )
from app.utils.enums import ApplicationStatus, DeliveryStatus, OrderStatus, RoleName, TransportType

DEMO_PASSWORD = "demo12345"
ADMIN_PHONE = "+992900100000"
CUSTOMER_PHONE = "+992900100001"
COURIER_PHONE = "+992900100002"

SELLERS = [
    {"phone": "+992900100011", "first_name": "Farrukh", "last_name": "Karimov",
     "store_name": "TechStore", "description": "Gadgets, electronics and car accessories."},
    {"phone": "+992900100012", "first_name": "Madina", "last_name": "Rahimova",
     "store_name": "Beauty Corner", "description": "Beauty, clothing, shoes and accessories."},
    {"phone": "+992900100013", "first_name": "Sardor", "last_name": "Nazarov",
     "store_name": "Happy Kids", "description": "Toys, books, sports and home goods."},
]

# category (name_en) -> store_name, [(name, description, brand, price TJS, quantity)]
PRODUCTS = {
    "Electronics": ("TechStore", [
        ("Wireless Headphones", "Over-ear headphones with noise cancelling and 30 h battery.", "Sony", "850", 12),
        ("Smart Watch", "Fitness tracking, heart-rate monitor and notifications.", "Xiaomi", "620", 8),
        ("Power Bank 20000 mAh", "Fast charging for two devices at once.", "Anker", "310", 25),
        ("Bluetooth Speaker", "Compact waterproof speaker with deep bass.", "JBL", "540", 2),
        ("USB-C Charger 65W", "Charges a laptop, tablet and phone.", "Baseus", "190", 30),
    ]),
    "Sports & Recreation": ("Happy Kids", [
        ("Yoga Mat", "Non-slip 6 mm mat with carrying strap.", "Decathlon", "160", 20),
        ("Adjustable Dumbbells 2x10 kg", "Quick-change plates for home workouts.", None, "720", 5),
        ("Football Size 5", "Machine-stitched ball for grass and turf.", "Adidas", "240", 15),
        ("Jump Rope", "Speed rope with ball bearings.", None, "60", 40),
        ("Camping Tent for 2", "Lightweight tent, sets up in five minutes.", "Quechua", "980", 0),
    ]),
    "Beauty & Care": ("Beauty Corner", [
        ("Moisturizing Face Cream", "Light daily cream with hyaluronic acid.", "Nivea", "95", 30),
        ("Argan Oil Shampoo", "Gentle shampoo for dry and colored hair.", "L'Oreal", "85", 25),
        ("Matte Lipstick", "Long-lasting matte finish, soft rose shade.", "Maybelline", "70", 18),
        ("Eau de Parfum 50 ml", "Fresh floral fragrance with citrus notes.", "Zara", "450", 1),
        ("Sunscreen SPF 50", "Water-resistant protection for face and body.", "La Roche-Posay", "210", 14),
    ]),
    "Home & Interior": ("Happy Kids", [
        ("Cotton Bed Linen Set", "Double size set, 100% cotton, soft pastel color.", None, "520", 10),
        ("LED Desk Lamp", "Three brightness levels and USB port.", "Xiaomi", "260", 12),
        ("Ceramic Mug Set of 4", "Matte glaze mugs, 350 ml each.", None, "180", 16),
        ("Scented Candle", "Soy wax candle, lavender, 40 hours.", None, "75", 22),
        ("Throw Blanket", "Warm fleece blanket 150x200 cm.", None, "230", 9),
    ]),
    "Clothing": ("Beauty Corner", [
        ("Cotton T-Shirt", "Classic fit, breathable cotton.", "Uniqlo", "120", 40),
        ("Denim Jacket", "Light blue denim with button front.", "Levi's", "690", 6),
        ("Knitted Sweater", "Soft wool blend, relaxed fit.", "H&M", "380", 11),
        ("Summer Dress", "Flowing midi dress in light fabric.", "Zara", "450", 7),
        ("Hoodie", "Fleece hoodie with front pocket.", None, "310", 2),
    ]),
    "Shoes": ("Beauty Corner", [
        ("Running Sneakers", "Cushioned sole for everyday running.", "Nike", "890", 9),
        ("Leather Loafers", "Genuine leather, comfortable insole.", None, "760", 4),
        ("Canvas Sneakers", "Low-top classic canvas shoes.", "Converse", "520", 13),
        ("Home Slippers", "Warm and soft, anti-slip sole.", None, "90", 25),
        ("Ankle Boots", "Suede ankle boots with low heel.", None, "980", 3),
    ]),
    "Accessories": ("Beauty Corner", [
        ("Leather Wallet", "Slim wallet with RFID protection.", None, "210", 15),
        ("Canvas Backpack", "15-inch laptop compartment, water repellent.", "Xiaomi", "390", 10),
        ("Sunglasses", "Polarized lenses with UV400 protection.", "Ray-Ban", "980", 2),
        ("Silk Scarf", "Lightweight scarf with soft print.", None, "160", 12),
        ("Wrist Watch", "Minimalist analog watch, leather strap.", "Casio", "540", 7),
    ]),
    "Books": ("Happy Kids", [
        ("The Little Prince", "Antoine de Saint-Exupery, illustrated edition.", None, "85", 20),
        ("Atomic Habits", "James Clear on building good habits.", None, "140", 15),
        ("Harry Potter and the Philosopher's Stone", "J. K. Rowling, hardcover.", None, "160", 12),
        ("English Grammar in Use", "Raymond Murphy, with answers.", None, "210", 8),
        ("Children's Encyclopedia", "Bright illustrated encyclopedia for ages 6+.", None, "260", 1),
    ]),
    "Kids": ("Happy Kids", [
        ("Building Blocks Set 500 pcs", "Colorful bricks compatible with major brands.", None, "350", 14),
        ("Plush Teddy Bear", "Soft 40 cm bear, safe for toddlers.", None, "130", 18),
        ("Jigsaw Puzzle 1000 pcs", "Landscape puzzle for the whole family.", "Ravensburger", "170", 10),
        ("Remote Control Car", "Rechargeable car with 2.4 GHz remote.", None, "290", 6),
        ("Wooden Train Set", "Track, bridge and three wagons.", None, "240", 0),
    ]),
    "Cars & Accessories": ("TechStore", [
        ("Car Phone Holder", "Magnetic holder for the air vent.", "Baseus", "80", 30),
        ("Dash Camera", "Full HD recording with night vision.", "Xiaomi", "640", 7),
        ("Car Vacuum Cleaner", "Cordless handheld vacuum, 120 W.", None, "330", 9),
        ("Seat Covers Set", "Universal fit, breathable fabric.", None, "560", 4),
        ("Tire Inflator", "Portable digital compressor, 12 V.", "Michelin", "420", 2),
    ]),
}

# Soft tints of the brand palette: (background, shape)
IMAGE_COLORS = [
    ("#D1E7F1", "#A9D2E3"), ("#D5CAF5", "#B7A7EC"), ("#CDEDE4", "#70C9B1"),
    ("#D6E8EE", "#8FBFCD"), ("#E6E1F8", "#C3B6F0"), ("#DDF1EA", "#9ED8C6"),
]
IMAGE_SIZE = (800, 600)  # 4:3 for every product, same as the card ratio


def placeholder_image(seed: str) -> bytes:
    """A calm abstract placeholder: two soft shapes, no text or badges."""
    rnd = random.Random(seed)
    background, shape = rnd.choice(IMAGE_COLORS)
    image = Image.new("RGB", IMAGE_SIZE, background)
    draw = ImageDraw.Draw(image)
    w, h = IMAGE_SIZE
    r = rnd.randint(140, 200)
    cx, cy = rnd.randint(w // 2 - 120, w // 2 + 120), rnd.randint(h // 2 - 60, h // 2 + 60)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=shape)
    side = rnd.randint(90, 140)
    x, y = rnd.randint(60, w - side - 60), rnd.randint(60, h - side - 60)
    draw.rounded_rectangle((x, y, x + side, y + side), radius=24, fill="#FFFFFF")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def get_or_register(db: Session, phone: str, first_name: str | None = None,
                    last_name: str | None = None) -> User:
    user = auth_service.get_user_by_phone(db, phone)
    if user is None:
        user = auth_service.register_user(db, UserRegister(
            phone_number=phone, password=DEMO_PASSWORD, password_confirm=DEMO_PASSWORD,
            first_name=first_name, last_name=last_name))
    return user


def ensure_admin(db: Session) -> User:
    user = get_or_register(db, ADMIN_PHONE, "Demo", "Admin")
    if not user.has_role(RoleName.ADMIN):
        user.roles.append(UserRole(role=RoleName.ADMIN))
        db.commit()
    return user


def ensure_seller(db: Session, data: dict) -> User:
    user = get_or_register(db, data["phone"])
    if not user.has_role(RoleName.SELLER):
        application = application_service.submit_seller_application(db, user, SellerApplicationCreate(
            first_name=data["first_name"], last_name=data["last_name"], phone_number=data["phone"],
            address="Rudaki Avenue, Dushanbe", store_name=data["store_name"],
            store_description=data["description"]))
        application_service.review_seller_application(
            db, application.id, ApplicationReview(status=ApplicationStatus.APPROVED))
        db.refresh(user)
    return user


def ensure_courier(db: Session) -> User:
    user = get_or_register(db, COURIER_PHONE)
    if not user.has_role(RoleName.COURIER):
        application = application_service.submit_courier_application(db, user, CourierApplicationCreate(
            first_name="Bakhtiyor", last_name="Saidov", phone_number=COURIER_PHONE,
            address="Somoni district, Dushanbe", transport_type=TransportType.MOTORCYCLE,
            experience="3 years of food and parcel delivery"))
        application_service.review_courier_application(
            db, application.id, ApplicationReview(status=ApplicationStatus.APPROVED))
        db.refresh(user)
    return user


def ensure_products(db: Session, sellers: dict[str, User]) -> dict[str, Product]:
    categories = {c.name_en: c for c in db.scalars(select(Category))}
    products: dict[str, Product] = {}
    for category_name, (store_name, items) in PRODUCTS.items():
        seller = sellers[store_name]
        for name, description, brand, price, quantity in items:
            product = db.scalar(select(Product).where(Product.seller_id == seller.id, Product.name == name))
            if product is None:
                product = product_service.create_product(db, seller, ProductCreate(
                    name=name, description=description, brand=brand, price=Decimal(price),
                    quantity=quantity, category_id=categories[category_name].id))
            if product.image is None:
                upload = UploadFile(file=io.BytesIO(placeholder_image(name)), filename="demo.png")
                product = product_service.set_product_image(db, seller.id, product.id, upload)
            products[name] = product
    return products


def place_order(db: Session, customer: User, lines: list[tuple[Product, int]]) -> Order:
    cart_service.clear_cart(db, customer.id)
    for product, quantity in lines:
        cart_service.add_item(db, customer.id, CartItemAdd(product_id=product.id, quantity=quantity))
    return order_service.create_order(db, customer, OrderCreate(
        recipient_name="Ali Valiev", phone_number=CUSTOMER_PHONE,
        address="Ismoili Somoni 15, apt. 4, Dushanbe", comment="Please call before delivery"))


def deliver(db: Session, order: Order, courier: User, steps: list[DeliveryStatus]) -> None:
    order_service.update_order_status(db, order.id, OrderStatus.CONFIRMED)
    delivery_service.assign_courier(db, order.id, courier.id)
    for step in steps:
        delivery_service.update_delivery_status(db, courier.id, order.id, step)


def ensure_orders(db: Session, customer: User, courier: User, p: dict[str, Product]) -> int:
    if db.scalar(select(Order.id).where(Order.user_id == customer.id).limit(1)) is not None:
        return 0
    full_delivery = [DeliveryStatus.PICKED_UP, DeliveryStatus.IN_DELIVERY, DeliveryStatus.DELIVERED]

    deliver(db, place_order(db, customer, [(p["Wireless Headphones"], 2), (p["Smart Watch"], 1)]),
            courier, full_delivery)
    deliver(db, place_order(db, customer, [(p["Building Blocks Set 500 pcs"], 3), (p["Yoga Mat"], 2)]),
            courier, full_delivery)
    deliver(db, place_order(db, customer, [(p["Moisturizing Face Cream"], 4), (p["Wireless Headphones"], 1)]),
            courier, full_delivery)
    deliver(db, place_order(db, customer, [(p["Running Sneakers"], 1), (p["Cotton T-Shirt"], 3)]),
            courier, [DeliveryStatus.PICKED_UP])                                    # shipped
    confirmed = place_order(db, customer, [(p["Plush Teddy Bear"], 2), (p["Atomic Habits"], 1)])
    order_service.update_order_status(db, confirmed.id, OrderStatus.CONFIRMED)    # confirmed
    place_order(db, customer, [(p["Power Bank 20000 mAh"], 1), (p["LED Desk Lamp"], 1)])  # pending
    cancelled = place_order(db, customer, [(p["Denim Jacket"], 1)])
    order_service.cancel_user_order(db, customer.id, cancelled.id)                 # cancelled
    return 7


def main():
    with SessionLocal() as db:
        created_categories = seed_categories(db)
        admin = ensure_admin(db)
        sellers = {data["store_name"]: ensure_seller(db, data) for data in SELLERS}
        courier = ensure_courier(db)
        customer = get_or_register(db, CUSTOMER_PHONE, "Ali", "Valiev")
        products = ensure_products(db, sellers)
        created_orders = ensure_orders(db, customer, courier, products)

    print(f"Categories created: {created_categories}")
    print(f"Products: {len(products)}, orders created: {created_orders}")
    print(f"\nDemo accounts (password for all: {DEMO_PASSWORD}) - local development only")
    print(f"  admin     {ADMIN_PHONE}")
    print(f"  customer  {CUSTOMER_PHONE}")
    print(f"  courier   {COURIER_PHONE}")
    for data in SELLERS:
        print(f"  seller    {data['phone']}  ({data['store_name']})")


if __name__ == "__main__":
    main()
