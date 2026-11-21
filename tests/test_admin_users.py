import pytest

from app.utils.enums import RoleName
from tests.conftest import auth


def test_list_users_with_roles(client, admin_headers, customer, seller):
    body = client.get("/admin/users", headers=admin_headers).json()
    assert body["total"] == 3
    roles = {u["id"]: u["roles"] for u in body["items"]}
    assert roles[seller.id] == ["seller"]
    assert roles[customer.id] == []


def test_search_by_phone(client, admin_headers, make_user):
    target = make_user(phone="+992911223344")
    make_user(phone="+992955555555")
    body = client.get("/admin/users", params={"q": "1122"}, headers=admin_headers).json()
    assert [u["id"] for u in body["items"]] == [target.id]


def test_filter_by_role_and_status(client, admin_headers, seller, make_user):
    make_user(is_active=False)
    sellers = client.get("/admin/users", params={"role": "seller"}, headers=admin_headers).json()
    assert [u["id"] for u in sellers["items"]] == [seller.id]
    blocked = client.get("/admin/users", params={"is_active": False}, headers=admin_headers).json()
    assert blocked["total"] == 1


def test_pagination(client, admin_headers, make_user):
    for _ in range(4):
        make_user()
    body = client.get("/admin/users", params={"limit": 2, "offset": 2}, headers=admin_headers).json()
    assert (len(body["items"]), body["total"]) == (2, 5)


def test_block_and_unblock(client, admin_headers, customer):
    headers = auth(customer)
    response = client.patch(f"/admin/users/{customer.id}", json={"is_active": False}, headers=admin_headers)
    assert response.status_code == 200 and response.json()["is_active"] is False
    assert client.get("/auth/me", headers=headers).status_code == 401
    client.patch(f"/admin/users/{customer.id}", json={"is_active": True}, headers=admin_headers)
    assert client.get("/auth/me", headers=headers).status_code == 200


def test_admin_cannot_block_self(client, admin, admin_headers):
    response = client.patch(f"/admin/users/{admin.id}", json={"is_active": False}, headers=admin_headers)
    assert response.status_code == 409


def test_missing_user(client, admin_headers):
    assert client.get("/admin/users/999", headers=admin_headers).status_code == 404
    assert client.patch("/admin/users/999", json={"is_active": False}, headers=admin_headers).status_code == 404


@pytest.mark.parametrize("method,url", [("GET", "/admin/users"), ("PATCH", "/admin/users/1")])
def test_admin_only(client, customer, method, url):
    response = client.request(method, url, json={"is_active": False}, headers=auth(customer))
    assert response.status_code == 403
