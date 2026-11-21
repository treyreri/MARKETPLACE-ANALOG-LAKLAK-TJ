"""Role x endpoint matrix (spec section 20). Checks access only, not business logic."""
import pytest

from app.utils.enums import RoleName
from tests.conftest import auth

ROLES = ["guest", "customer", "seller", "courier", "admin"]


@pytest.fixture
def headers_for(make_user, make_seller, make_courier):
    def _headers(role: str) -> dict[str, str]:
        if role == "guest":
            return {}
        if role == "customer":
            return auth(make_user())
        if role == "seller":
            return auth(make_seller())
        if role == "courier":
            return auth(make_courier())
        return auth(make_user(RoleName.ADMIN))
    return _headers


def expected(allowed: set[str], ok: int = 200):
    """guest -> 401, allowed roles -> ok, everyone else -> 403."""
    return {role: ok if role in allowed else (401 if role == "guest" else 403) for role in ROLES}


EVERYONE = set(ROLES)
AUTHENTICATED = EVERYONE - {"guest"}

CASES = [
    # public catalog
    ("GET", "/products", None, {r: 200 for r in ROLES}),
    ("GET", "/products/search?q=x", None, {r: 200 for r in ROLES}),
    ("GET", "/categories", None, {r: 200 for r in ROLES}),
    # any registered user
    ("GET", "/auth/me", None, expected(AUTHENTICATED)),
    ("GET", "/cart", None, expected(AUTHENTICATED)),
    ("GET", "/orders", None, expected(AUTHENTICATED)),
    # seller only
    ("GET", "/seller/products", None, expected({"seller"})),
    ("GET", "/seller/orders", None, expected({"seller"})),
    ("GET", "/seller/store", None, expected({"seller"})),
    # courier only
    ("GET", "/courier/orders", None, expected({"courier"})),
    ("GET", "/courier/profile", None, expected({"courier"})),
    # admin only
    ("GET", "/admin/orders", None, expected({"admin"})),
    ("GET", "/admin/seller-applications", None, expected({"admin"})),
    ("GET", "/admin/courier-applications", None, expected({"admin"})),
    ("GET", "/admin/couriers", None, expected({"admin"})),
    ("POST", "/categories", {"name_ru": "Книги", "name_en": "Books"}, expected({"admin"}, ok=201)),
]


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize(
    "method,url,body,statuses", CASES, ids=[f"{m} {u}" for m, u, _, _ in CASES])
def test_access(client, headers_for, role, method, url, body, statuses):
    response = client.request(method, url, json=body, headers=headers_for(role))
    assert response.status_code == statuses[role]


@pytest.mark.parametrize("role", ROLES)
def test_create_product_only_seller(client, headers_for, category, role):
    body = {"name": "Book", "price": "10", "quantity": 1, "category_id": category.id}
    response = client.post("/seller/products", json=body, headers=headers_for(role))
    assert response.status_code == expected({"seller"}, ok=201)[role]


@pytest.mark.parametrize("role", ["guest", "customer"])
def test_apply_requires_login(client, headers_for, category, role):
    body = {
        "first_name": "A", "last_name": "B", "phone_number": "+992900000777",
        "address": "Dushanbe", "store_name": "Shop", }
    response = client.post("/seller/applications", json=body, headers=headers_for(role))
    assert response.status_code == {"guest": 401, "customer": 201}[role]


@pytest.mark.parametrize("role", ROLES)
def test_category_delete_only_admin(client, headers_for, category, role):
    response = client.delete(f"/categories/{category.id}", headers=headers_for(role))
    assert response.status_code == expected({"admin"}, ok=204)[role]


def test_pending_seller_cannot_create_products(client, customer, category):
    application = {
        "first_name": "A", "last_name": "B", "phone_number": "+992900000777",
        "address": "Dushanbe", "store_name": "Shop", }
    client.post("/seller/applications", json=application, headers=auth(customer))
    body = {"name": "Book", "price": "10", "quantity": 1, "category_id": category.id}
    assert client.post("/seller/products", json=body, headers=auth(customer)).status_code == 403
