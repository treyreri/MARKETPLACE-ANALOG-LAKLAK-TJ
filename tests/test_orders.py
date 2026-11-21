from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import Order, Product
from tests.conftest import auth

CHECKOUT = {
    "recipient_name": "Ali Valiev", "phone_number": "+992900000001",
    "address": "Rudaki 1, Dushanbe", "comment": "Call before delivery", }


def add(client, headers, product, quantity=1):
    response = client.post(
        "/cart/items", json={"product_id": product.id, "quantity": quantity}, headers=headers)
    assert response.status_code == 200
    return response


def checkout(client, headers):
    return client.post("/orders", json=CHECKOUT, headers=headers)


@pytest.fixture
def watch(make_product, seller, category):
    return make_product(seller, category, name="Smart Watch", price=Decimal("400"), quantity=3)


@pytest.fixture
def order(client, customer_headers, product):
    add(client, customer_headers, product, 2)
    return checkout(client, customer_headers).json()


def set_status(client, headers, order_id, status):
    return client.patch(f"/admin/orders/{order_id}", json={"status": status}, headers=headers)


# checkout

def test_checkout(client, db, customer_headers, product, watch, seller):
    add(client, customer_headers, product, 2)
    add(client, customer_headers, watch, 1)
    response = checkout(client, customer_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["payment_method"] == "cash_on_delivery"
    assert body["total_price"] == "900.00"
    assert body["recipient_name"] == CHECKOUT["recipient_name"]
    items = {i["product_name"]: i for i in body["items"]}
    assert items["Wireless Headphones"]["price"] == "250.00"
    assert items["Wireless Headphones"]["quantity"] == 2
    assert items["Wireless Headphones"]["line_total"] == "500.00"

    db.expire_all()
    assert db.get(Product, product.id).quantity == 3
    assert db.get(Product, watch.id).quantity == 2
    assert client.get("/cart", headers=customer_headers).json()["items"] == []


def test_checkout_empty_cart(client, customer_headers):
    assert checkout(client, customer_headers).status_code == 400


@pytest.mark.parametrize("field,value", [("phone_number", "123"), ("address", ""), ("recipient_name", "")])
def test_checkout_invalid_form(client, customer_headers, product, field, value):
    add(client, customer_headers, product)
    response = client.post("/orders", json={**CHECKOUT, field: value}, headers=customer_headers)
    assert response.status_code == 422


def test_checkout_is_atomic_when_second_item_out_of_stock(client, db, customer_headers, product, watch):
    add(client, customer_headers, product, 2)
    add(client, customer_headers, watch, 3)
    watch.quantity = 1  # someone bought the watches meanwhile
    db.commit()

    response = checkout(client, customer_headers)

    assert response.status_code == 400
    assert "Smart Watch" in response.json()["detail"]
    db.expire_all()
    assert db.get(Product, product.id).quantity == 5  # first item not deducted
    assert db.get(Product, watch.id).quantity == 1
    assert len(client.get("/cart", headers=customer_headers).json()["items"]) == 2  # cart kept
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_checkout_is_atomic_when_product_hidden(client, db, customer_headers, product, watch):
    add(client, customer_headers, product, 1)
    add(client, customer_headers, watch, 1)
    watch.is_active = False
    db.commit()

    assert checkout(client, customer_headers).status_code == 400
    db.expire_all()
    assert db.get(Product, product.id).quantity == 5
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_order_keeps_price_snapshot(client, db, customer_headers, seller_headers, order, product):
    client.patch(f"/seller/products/{product.id}",
                 json={"price": "999", "name": "Renamed"}, headers=seller_headers)
    body = client.get(f"/orders/{order['id']}", headers=customer_headers).json()
    assert body["items"][0]["price"] == "250.00"
    assert body["items"][0]["product_name"] == "Wireless Headphones"
    assert body["total_price"] == "500.00"


def test_order_survives_product_deletion(client, customer_headers, seller_headers, order, product):
    client.delete(f"/seller/products/{product.id}", headers=seller_headers)
    item = client.get(f"/orders/{order['id']}", headers=customer_headers).json()["items"][0]
    assert item["product_id"] is None
    assert item["product_name"] == "Wireless Headphones"


def test_datetimes_serialized_with_timezone(client, customer_headers, order):
    created_at = client.get(f"/orders/{order['id']}", headers=customer_headers).json()["created_at"]
    assert datetime.fromisoformat(created_at).tzinfo is not None


# customer views

def test_list_my_orders_newest_first(client, customer_headers, product):
    ids = []
    for _ in range(2):
        add(client, customer_headers, product)
        ids.append(checkout(client, customer_headers).json()["id"])
    assert [o["id"] for o in client.get("/orders", headers=customer_headers).json()] == ids[::-1]


def test_other_users_order_is_404(client, make_user, order):
    other = auth(make_user())
    assert client.get(f"/orders/{order['id']}", headers=other).status_code == 404
    assert client.post(f"/orders/{order['id']}/cancel", headers=other).status_code == 404
    assert client.get("/orders", headers=other).json() == []


def test_customer_cancels_pending_order_and_restocks(client, db, customer_headers, order, product):
    response = client.post(f"/orders/{order['id']}/cancel", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    db.expire_all()
    assert db.get(Product, product.id).quantity == 5


def test_customer_cannot_cancel_confirmed_order(client, db, customer_headers, admin_headers, order, product):
    set_status(client, admin_headers, order["id"], "confirmed")
    response = client.post(f"/orders/{order['id']}/cancel", headers=customer_headers)
    assert response.status_code == 409
    db.expire_all()
    assert db.get(Product, product.id).quantity == 3  # no double restock


# admin status transitions

def test_admin_full_status_chain_without_courier(client, admin_headers, order):
    for status in ["confirmed", "processing", "shipped", "delivered"]:
        response = set_status(client, admin_headers, order["id"], status)
        assert response.status_code == 200, status
        assert response.json()["status"] == status


@pytest.mark.parametrize("path,target", [
    ([], "processing"),
    ([], "shipped"),
    ([], "delivered"),
    (["confirmed"], "pending"),
    (["confirmed", "processing", "shipped"], "cancelled"),
    (["confirmed", "processing", "shipped", "delivered"], "cancelled"),
    (["cancelled"], "confirmed"),
])
def test_admin_forbidden_transitions(client, admin_headers, order, path, target):
    for status in path:
        set_status(client, admin_headers, order["id"], status)
    assert set_status(client, admin_headers, order["id"], target).status_code == 409


@pytest.mark.parametrize("path", [[], ["confirmed"], ["confirmed", "processing"]])
def test_admin_cancel_restocks(client, db, admin_headers, order, product, path):
    for status in path:
        set_status(client, admin_headers, order["id"], status)
    assert set_status(client, admin_headers, order["id"], "cancelled").status_code == 200
    db.expire_all()
    assert db.get(Product, product.id).quantity == 5


def test_admin_list_orders_with_filter(client, admin_headers, customer_headers, product):
    for _ in range(2):
        add(client, customer_headers, product)
        checkout(client, customer_headers)
    first_id = client.get("/admin/orders", headers=admin_headers).json()[-1]["id"]
    set_status(client, admin_headers, first_id, "confirmed")

    assert len(client.get("/admin/orders", headers=admin_headers).json()) == 2
    confirmed = client.get("/admin/orders", params={"status": "confirmed"}, headers=admin_headers)
    assert [o["id"] for o in confirmed.json()] == [first_id]


def test_admin_missing_order(client, admin_headers):
    assert client.get("/admin/orders/999", headers=admin_headers).status_code == 404
    assert set_status(client, admin_headers, 999, "confirmed").status_code == 404


# seller view

def test_seller_sees_only_own_order_lines(client, make_seller, make_product, category,
                                          customer_headers, seller_headers, product):
    other_seller = make_seller(store_name="Other")
    foreign = make_product(other_seller, category, name="Foreign", price=Decimal("10"))
    add(client, customer_headers, product, 2)
    add(client, customer_headers, foreign, 1)
    order_id = checkout(client, customer_headers).json()["id"]

    orders = client.get("/seller/orders", headers=seller_headers).json()
    assert len(orders) == 1
    assert orders[0]["order_id"] == order_id
    assert [i["product_name"] for i in orders[0]["items"]] == ["Wireless Headphones"]
    assert orders[0]["total"] == "500.00"
    other_orders = client.get("/seller/orders", headers=auth(other_seller)).json()
    assert other_orders[0]["total"] == "10.00"


def test_datetimes_are_aware_after_reload(db, client, customer_headers, admin_headers, order):
    client.patch(f"/admin/orders/{order['id']}", json={"status": "confirmed"}, headers=admin_headers)
    db.expire_all()
    stored = db.get(Order, order["id"])
    assert stored.created_at.tzinfo is not None
    assert stored.updated_at.utcoffset().total_seconds() == 0
