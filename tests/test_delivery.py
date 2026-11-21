from datetime import datetime

import pytest

from app.models import Order, Product
from app.utils.enums import RoleName
from tests.conftest import auth

CHECKOUT = {"recipient_name": "Ali", "phone_number": "+992900000001", "address": "Rudaki 1"}


@pytest.fixture
def order_id(client, customer_headers, product):
    client.post("/cart/items", json={"product_id": product.id, "quantity": 2}, headers=customer_headers)
    return client.post("/orders", json=CHECKOUT, headers=customer_headers).json()["id"]


@pytest.fixture
def confirmed(client, admin_headers, order_id):
    set_status(client, admin_headers, order_id, "confirmed")
    return order_id


@pytest.fixture
def assigned(client, admin_headers, confirmed, courier):
    assert assign(client, admin_headers, confirmed, courier.id).status_code == 200
    return confirmed


def set_status(client, headers, order_id, status):
    return client.patch(f"/admin/orders/{order_id}", json={"status": status}, headers=headers)


def assign(client, headers, order_id, courier_id):
    return client.post(f"/admin/orders/{order_id}/assign-courier",
                       json={"courier_id": courier_id}, headers=headers)


def deliver(client, headers, order_id, status):
    return client.patch(f"/courier/orders/{order_id}/status", json={"status": status}, headers=headers)


# assignment

def test_assign_confirmed_order(client, db, admin_headers, confirmed, courier):
    response = assign(client, admin_headers, confirmed, courier.id)
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert response.json()["courier_id"] == courier.id
    order = db.get(Order, confirmed)
    db.refresh(order)
    assert order.delivery_status == "assigned"
    assert order.assigned_at is not None


def test_assign_processing_order(client, admin_headers, confirmed, courier):
    set_status(client, admin_headers, confirmed, "processing")
    response = assign(client, admin_headers, confirmed, courier.id)
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


@pytest.mark.parametrize("path", [[], ["cancelled"], ["confirmed", "processing", "shipped"]])
def test_assign_requires_confirmed_or_processing(client, admin_headers, order_id, courier, path):
    for status in path:
        set_status(client, admin_headers, order_id, status)
    assert assign(client, admin_headers, order_id, courier.id).status_code == 409


def test_assign_non_courier(client, admin_headers, confirmed, customer):
    assert assign(client, admin_headers, confirmed, customer.id).status_code == 400


def test_assign_blocked_courier(client, make_courier, admin_headers, confirmed):
    blocked = make_courier(is_active=False)
    assert assign(client, admin_headers, confirmed, blocked.id).status_code == 400


def test_assign_missing_courier_or_order(client, admin_headers, confirmed, courier):
    assert assign(client, admin_headers, confirmed, 999).status_code == 400
    assert assign(client, admin_headers, 999, courier.id).status_code == 404


def test_reassign_before_pickup(client, make_courier, admin_headers, assigned, courier):
    other = make_courier()
    assert assign(client, admin_headers, assigned, other.id).json()["courier_id"] == other.id
    assert client.get(f"/courier/orders/{assigned}", headers=auth(courier)).status_code == 404
    assert client.get(f"/courier/orders/{assigned}", headers=auth(other)).status_code == 200


def test_cannot_reassign_after_pickup(client, make_courier, admin_headers, courier_headers, assigned):
    deliver(client, courier_headers, assigned, "picked_up")
    assert assign(client, admin_headers, assigned, make_courier().id).status_code == 409


def test_admin_lists_active_couriers(client, make_courier, admin_headers, courier):
    make_courier(is_active=False)
    couriers = client.get("/admin/couriers", headers=admin_headers).json()
    assert [c["id"] for c in couriers] == [courier.id]
    assert couriers[0]["transport_type"] == "bicycle"


# courier side

def test_courier_sees_assigned_order_details(client, courier_headers, assigned):
    orders = client.get("/courier/orders", headers=courier_headers).json()
    assert [o["id"] for o in orders] == [assigned]
    order = orders[0]
    assert order["address"] == CHECKOUT["address"]
    assert order["phone_number"] == CHECKOUT["phone_number"]
    assert order["delivery_status"] == "assigned"
    assert order["items"][0]["product_name"] == "Wireless Headphones"


def test_other_courier_cannot_see_or_update(client, make_courier, assigned):
    other = auth(make_courier())
    assert client.get("/courier/orders", headers=other).json() == []
    assert client.get(f"/courier/orders/{assigned}", headers=other).status_code == 404
    assert deliver(client, other, assigned, "picked_up").status_code == 404


def test_delivery_steps_sync_order_status(client, db, courier_headers, assigned):
    expected = [("picked_up", "shipped"), ("in_delivery", "shipped"), ("delivered", "delivered")]
    for delivery_status, order_status in expected:
        response = deliver(client, courier_headers, assigned, delivery_status)
        assert response.status_code == 200, delivery_status
        assert response.json()["delivery_status"] == delivery_status
        assert response.json()["status"] == order_status
    assert response.json()["delivered_at"] is not None


@pytest.mark.parametrize("done,target", [
    ([], "in_delivery"),
    ([], "delivered"),
    ([], "assigned"),
    (["picked_up"], "picked_up"),
    (["picked_up"], "assigned"),
    (["picked_up", "in_delivery", "delivered"], "delivered"),
])
def test_delivery_status_must_be_sequential(client, courier_headers, assigned, done, target):
    for status in done:
        deliver(client, courier_headers, assigned, status)
    assert deliver(client, courier_headers, assigned, target).status_code == 409


def test_delivered_orders_hidden_from_active_list(client, courier_headers, assigned):
    for status in ["picked_up", "in_delivery", "delivered"]:
        deliver(client, courier_headers, assigned, status)
    assert client.get("/courier/orders", headers=courier_headers).json() == []
    history = client.get("/courier/orders", params={"active_only": False}, headers=courier_headers)
    assert [o["id"] for o in history.json()] == [assigned]


def test_admin_cannot_cancel_after_pickup(client, admin_headers, courier_headers, assigned):
    deliver(client, courier_headers, assigned, "picked_up")
    assert set_status(client, admin_headers, assigned, "cancelled").status_code == 409


@pytest.mark.parametrize("done,target", [([], "shipped"), (["picked_up"], "delivered")])
def test_admin_cannot_set_courier_managed_status(client, admin_headers, courier_headers, assigned, done, target):
    for status in done:
        deliver(client, courier_headers, assigned, status)
    assert set_status(client, admin_headers, assigned, target).status_code == 409


def test_admin_cancel_assigned_order_resets_delivery(client, db, admin_headers, courier_headers, assigned, product):
    response = set_status(client, admin_headers, assigned, "cancelled")
    assert response.status_code == 200
    assert response.json()["courier_id"] is None
    db.expire_all()
    order = db.get(Order, assigned)
    assert (order.delivery_status, order.assigned_at) == (None, None)
    assert db.get(Product, product.id).quantity == 5
    assert client.get("/courier/orders", headers=courier_headers).json() == []
