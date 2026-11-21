import pytest

from app.utils.enums import RoleName
from tests.conftest import auth

SELLER_APP = {
    "first_name": "Sam", "last_name": "Lee", "phone_number": "+992900000300",
    "address": "Dushanbe", "store_name": "TechStore", "store_description": "Gadgets",
    "additional_info": "since 2020", }
COURIER_APP = {
    "first_name": "Cid", "last_name": "Ray", "phone_number": "+992900000500",
    "address": "Dushanbe", "transport_type": "bicycle", "experience": "2 years", }

# kind -> (submit url, admin url, body, role, profile attribute)
KINDS = {
    "seller": ("/seller/applications", "/admin/seller-applications", SELLER_APP,
               RoleName.SELLER, "seller_profile"),
    "courier": ("/courier/applications", "/admin/courier-applications", COURIER_APP,
                RoleName.COURIER, "courier_profile"),
}


@pytest.fixture(params=list(KINDS))
def kind(request):
    return request.param


def submit(client, kind, headers):
    url, _, body, _, _ = KINDS[kind]
    return client.post(url, json=body, headers=headers)


def review(client, kind, application_id, headers, status, comment=None):
    _, admin_url, _, _, _ = KINDS[kind]
    return client.patch(f"{admin_url}/{application_id}",
                        json={"status": status, "admin_comment": comment}, headers=headers)


def test_submit(client, kind, customer_headers):
    response = submit(client, kind, customer_headers)
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["reviewed_at"] is None


def test_second_pending_is_conflict(client, kind, customer_headers):
    submit(client, kind, customer_headers)
    assert submit(client, kind, customer_headers).status_code == 409


def test_my_application(client, kind, customer_headers):
    url = KINDS[kind][0]
    assert client.get(f"{url}/me", headers=customer_headers).status_code == 404
    submit(client, kind, customer_headers)
    response = client.get(f"{url}/me", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_approve_grants_role_and_profile(client, db, kind, customer, customer_headers, admin_headers):
    application_id = submit(client, kind, customer_headers).json()["id"]
    response = review(client, kind, application_id, admin_headers, "approved", "welcome")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["admin_comment"] == "welcome"
    assert response.json()["reviewed_at"] is not None
    _, _, body, role, profile_attr = KINDS[kind]
    db.expire_all()
    assert customer.has_role(role)
    profile = getattr(customer, profile_attr)
    assert profile is not None and profile.address == body["address"]
    assert role.value in client.get("/auth/me", headers=customer_headers).json()["roles"]


def test_approved_seller_profile_copies_store(client, db, customer, customer_headers, admin_headers):
    application_id = submit(client, "seller", customer_headers).json()["id"]
    review(client, "seller", application_id, admin_headers, "approved")
    store = client.get("/seller/store", headers=customer_headers).json()
    assert store["store_name"] == "TechStore"
    assert store["store_description"] == "Gadgets"


def test_approved_seller_can_create_products(client, customer_headers, admin_headers, category):
    application_id = submit(client, "seller", customer_headers).json()["id"]
    review(client, "seller", application_id, admin_headers, "approved")
    body = {"name": "Book", "price": "10", "quantity": 1, "category_id": category.id}
    assert client.post("/seller/products", json=body, headers=customer_headers).status_code == 201


def test_reject(client, db, kind, customer, customer_headers, admin_headers):
    application_id = submit(client, kind, customer_headers).json()["id"]
    response = review(client, kind, application_id, admin_headers, "rejected", "incomplete")

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    db.expire_all()
    assert not customer.has_role(KINDS[kind][3])
    assert getattr(customer, KINDS[kind][4]) is None


def test_can_reapply_after_reject(client, kind, customer_headers, admin_headers):
    first = submit(client, kind, customer_headers).json()["id"]
    review(client, kind, first, admin_headers, "rejected")
    response = submit(client, kind, customer_headers)
    assert response.status_code == 201
    url = KINDS[kind][0]
    assert client.get(f"{url}/me", headers=customer_headers).json()["id"] == response.json()["id"]


def test_cannot_apply_when_role_granted(client, kind, customer_headers, admin_headers):
    application_id = submit(client, kind, customer_headers).json()["id"]
    review(client, kind, application_id, admin_headers, "approved")
    assert submit(client, kind, customer_headers).status_code == 409


@pytest.mark.parametrize("second", ["approved", "rejected"])
def test_re_review_is_conflict(client, kind, customer_headers, admin_headers, second):
    application_id = submit(client, kind, customer_headers).json()["id"]
    review(client, kind, application_id, admin_headers, "approved")
    assert review(client, kind, application_id, admin_headers, second).status_code == 409


def test_review_to_pending_rejected_by_schema(client, kind, customer_headers, admin_headers):
    application_id = submit(client, kind, customer_headers).json()["id"]
    assert review(client, kind, application_id, admin_headers, "pending").status_code == 422


def test_review_missing_application(client, kind, admin_headers):
    assert review(client, kind, 999, admin_headers, "approved").status_code == 404


def test_admin_list_filter_by_status(client, kind, make_user, admin_headers):
    first = auth(make_user())
    second = auth(make_user())
    approved_id = submit(client, kind, first).json()["id"]
    submit(client, kind, second)
    review(client, kind, approved_id, admin_headers, "approved")

    admin_url = KINDS[kind][1]
    assert len(client.get(admin_url, headers=admin_headers).json()) == 2
    pending = client.get(admin_url, params={"status": "pending"}, headers=admin_headers).json()
    assert [a["status"] for a in pending] == ["pending"]


def test_admin_get_application(client, kind, customer_headers, admin_headers):
    application_id = submit(client, kind, customer_headers).json()["id"]
    admin_url = KINDS[kind][1]
    assert client.get(f"{admin_url}/{application_id}", headers=admin_headers).status_code == 200
    assert client.get(f"{admin_url}/999", headers=admin_headers).status_code == 404


def test_seller_application_unknown_category(client, customer_headers):
    body = {**SELLER_APP, "category_id": 999}
    assert client.post("/seller/applications", json=body, headers=customer_headers).status_code == 400


def test_courier_application_invalid_transport(client, customer_headers):
    body = {**COURIER_APP, "transport_type": "rocket"}
    assert client.post("/courier/applications", json=body, headers=customer_headers).status_code == 422


def test_approve_fills_missing_user_names(client, db, kind, make_user, admin_headers):
    user = make_user()  # registered without first/last name
    application_id = submit(client, kind, auth(user)).json()["id"]
    review(client, kind, application_id, admin_headers, "approved")
    db.expire_all()
    body = KINDS[kind][2]
    assert (user.first_name, user.last_name) == (body["first_name"], body["last_name"])


def test_approve_keeps_existing_user_names(client, db, customer, customer_headers, admin_headers):
    application_id = submit(client, "courier", customer_headers).json()["id"]
    review(client, "courier", application_id, admin_headers, "approved")
    db.expire_all()
    assert customer.first_name == "Ali"
