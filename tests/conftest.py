import itertools
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  registers all models on Base.metadata
from app.database import Base, configure_sqlite, get_db
from app.main import app
from app.models import Category, CourierProfile, Product, SellerProfile, User, UserRole
from app.utils import files, security
from app.utils.enums import RoleName, TransportType
from app.utils.security import create_access_token, hash_password

PASSWORD = "secret123"
_phones = itertools.count(1)

# Production argon2 parameters are deliberately slow; tests only need a real hash
security.password_hasher = PasswordHash((Argon2Hasher(time_cost=1, memory_cost=8, parallelism=1),))


@pytest.fixture
def engine():
    # One shared in-memory connection (StaticPool), fresh schema per test
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool, )
    event.listen(engine, "connect", configure_sqlite)  # FK pragma + unicode lower()
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory) -> Session:
    """Session for arranging data and asserting DB state directly."""
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def image_dir(tmp_path, monkeypatch):
    """Keep uploaded files out of the project's uploads/ folder."""
    path = tmp_path / "products"
    monkeypatch.setattr(files, "PRODUCT_IMAGE_DIR", path)
    return path


# factories

def new_phone() -> str:
    return f"+99290{next(_phones):07d}"


@pytest.fixture
def make_user(db):
    def _make_user(*roles: RoleName, phone: str | None = None, is_active: bool = True, **fields) -> User:
        user = User(
            phone_number=phone or new_phone(),
            password_hash=hash_password(PASSWORD),
            is_active=is_active,
            **fields, )
        user.roles = [UserRole(role=role) for role in roles]
        db.add(user)
        db.commit()
        return user
    return _make_user


@pytest.fixture
def make_seller(db, make_user):
    def _make_seller(store_name: str = "TechStore", **fields) -> User:
        user = make_user(RoleName.SELLER, **fields)
        user.seller_profile = SellerProfile(
            store_name=store_name, address="Dushanbe", phone_number=user.phone_number)
        db.commit()
        return user
    return _make_seller


@pytest.fixture
def make_courier(db, make_user):
    def _make_courier(**fields) -> User:
        user = make_user(RoleName.COURIER, **fields)
        user.courier_profile = CourierProfile(
            phone_number=user.phone_number, address="Dushanbe", transport_type=TransportType.BICYCLE)
        db.commit()
        return user
    return _make_courier


@pytest.fixture
def make_product(db):
    def _make_product(seller: User, category: Category, **fields) -> Product:
        values = {"name": "Wireless Headphones", "price": Decimal("250.00"), "quantity": 5}
        values.update(fields)
        product = Product(seller_id=seller.id, category_id=category.id, **values)
        db.add(product)
        db.commit()
        return product
    return _make_product


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


# ready-made actors

@pytest.fixture
def customer(make_user):
    return make_user(first_name="Ali")


@pytest.fixture
def admin(make_user):
    return make_user(RoleName.ADMIN)


@pytest.fixture
def seller(make_seller):
    return make_seller()


@pytest.fixture
def courier(make_courier):
    return make_courier()


@pytest.fixture
def customer_headers(customer):
    return auth(customer)


@pytest.fixture
def admin_headers(admin):
    return auth(admin)


@pytest.fixture
def seller_headers(seller):
    return auth(seller)


@pytest.fixture
def courier_headers(courier):
    return auth(courier)


@pytest.fixture
def category(db):
    category = Category(name_ru="Электроника", name_en="Electronics")
    db.add(category)
    db.commit()
    return category


@pytest.fixture
def product(make_product, seller, category):
    return make_product(seller, category)
