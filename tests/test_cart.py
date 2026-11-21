from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Cart
from app.services import cart_service
from tests.conftest import auth


def add(client, headers, product, quantity=1):
    return client.post("/cart/items", json={"product_id": product.id, "quantity": quantity}, headers=headers)


def test_empty_cart(client, customer_headers):
    body = client.get("/cart", headers=customer_headers).json()
    assert body["items"] == []
    assert body["total_price"] == "0"
    assert body["can_checkout"] is False


def test_add_item(client, customer_headers, product):
    response = add(client, customer_headers, product, 2)
    assert response.status_code == 200
    body = response.json()
    assert body["total_quantity"] == 2
    assert body["total_price"] == "500.00"
    item = body["items"][0]
    assert (item["quantity"], item["line_total"], item["is_valid"]) == (2, "500.00", True)
    assert item["product"]["available_quantity"] == 5


def test_add_same_product_accumulates(client, customer_headers, product):
    add(client, customer_headers, product, 2)
    body = add(client, customer_headers, product, 3).json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 5


def test_add_more_than_stock(client, customer_headers, product):
    response = add(client, customer_headers, product, 6)
    assert response.status_code == 400
    assert "5" in response.json()["detail"]


def test_accumulated_quantity_respects_stock(client, customer_headers, product):
    add(client, customer_headers, product, 3)
    assert add(client, customer_headers, product, 3).status_code == 400
    assert client.get("/cart", headers=customer_headers).json()["items"][0]["quantity"] == 3


def test_cannot_add_own_product(client, seller_headers, product):
    assert add(client, seller_headers, product).status_code == 400


def test_cannot_add_inactive_product(client, db, customer_headers, product):
    product.is_active = False
    db.commit()
    assert add(client, customer_headers, product).status_code == 404


def test_cannot_add_missing_product(client, customer_headers):
    response = client.post("/cart/items", json={"product_id": 999}, headers=customer_headers)
    assert response.status_code == 404


@pytest.mark.parametrize("quantity", [0, -1, 101])
def test_add_invalid_quantity(client, customer_headers, product, quantity):
    assert add(client, customer_headers, product, quantity).status_code == 422


def test_total_for_several_products(client, customer_headers, make_product, seller, category, product):
    watch = make_product(seller, category, name="Smart Watch", price=Decimal("400"), quantity=1)
    add(client, customer_headers, product, 2)
    body = add(client, customer_headers, watch, 1).json()
    assert body["total_price"] == "900.00"  # spec section 10 example
    assert body["total_quantity"] == 3


def test_update_item_quantity(client, customer_headers, product):
    item_id = add(client, customer_headers, product, 1).json()["items"][0]["id"]
    response = client.patch(f"/cart/items/{item_id}", json={"quantity": 4}, headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["total_price"] == "1000.00"


def test_update_item_over_stock(client, customer_headers, product):
    item_id = add(client, customer_headers, product, 1).json()["items"][0]["id"]
    response = client.patch(f"/cart/items/{item_id}", json={"quantity": 6}, headers=customer_headers)
    assert response.status_code == 400


def test_remove_item(client, customer_headers, product):
    item_id = add(client, customer_headers, product).json()["items"][0]["id"]
    response = client.delete(f"/cart/items/{item_id}", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_clear_cart(client, customer_headers, product):
    add(client, customer_headers, product)
    assert client.delete("/cart", headers=customer_headers).json()["items"] == []


@pytest.mark.parametrize("method,body", [("PATCH", {"quantity": 1}), ("DELETE", None)])
def test_other_users_item_is_404(client, make_user, customer_headers, product, method, body):
    item_id = add(client, customer_headers, product).json()["items"][0]["id"]
    other = auth(make_user())
    response = client.request(method, f"/cart/items/{item_id}", json=body, headers=other)
    assert response.status_code == 404
    assert len(client.get("/cart", headers=customer_headers).json()["items"]) == 1


def test_item_invalid_after_stock_decrease(client, db, customer_headers, product):
    add(client, customer_headers, product, 3)
    product.quantity = 2
    db.commit()
    body = client.get("/cart", headers=customer_headers).json()
    assert body["items"][0]["is_valid"] is False
    assert body["items"][0]["product"]["available_quantity"] == 2
    assert body["can_checkout"] is False


def test_item_invalid_after_product_hidden(client, db, customer_headers, product):
    add(client, customer_headers, product)
    product.is_active = False
    db.commit()
    body = client.get("/cart", headers=customer_headers).json()
    assert body["items"][0]["is_valid"] is False
    assert body["can_checkout"] is False


def test_cart_persists_between_requests(client, customer_headers, product):
    cart_id = add(client, customer_headers, product).json()["id"]
    assert client.get("/cart", headers=customer_headers).json()["id"] == cart_id


def test_product_deleted_removes_cart_item(client, customer_headers, seller_headers, product):
    add(client, customer_headers, product)
    client.delete(f"/seller/products/{product.id}", headers=seller_headers)
    assert client.get("/cart", headers=customer_headers).json()["items"] == []


@pytest.mark.xfail(reason="#11: concurrent get_or_create_cart -> IntegrityError -> 500")
def test_get_or_create_cart_race(db, session_factory, customer):
    # Another request created the cart after this one looked it up
    with session_factory() as other:
        cart_service.get_or_create_cart(other, customer.id)
    original_scalar = db.scalar
    db.scalar = lambda stmt, *a, **kw: None  # lookup that ran before the other commit
    cart = cart_service.get_or_create_cart(db, customer.id)
    db.scalar = original_scalar
    assert cart.id == db.scalar(select(Cart.id).where(Cart.user_id == customer.id))
