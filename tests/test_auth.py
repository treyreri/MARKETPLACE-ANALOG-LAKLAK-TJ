import pytest

from app.services import auth_service
from tests.conftest import PASSWORD, auth

REGISTER = {
    "phone_number": "+992900000001",
    "password": PASSWORD,
    "password_confirm": PASSWORD,
    "first_name": "Alex",
    "last_name": "Smith",
}


def login(client, phone, password=PASSWORD):
    return client.post("/auth/login", json={"phone_number": phone, "password": password})


def test_register(client, db):
    response = client.post("/auth/register", json=REGISTER)

    assert response.status_code == 201
    body = response.json()
    assert body["phone_number"] == REGISTER["phone_number"]
    assert body["first_name"] == "Alex"
    assert body["roles"] == []
    assert "password" not in body and "password_hash" not in body
    stored = auth_service.get_user_by_phone(db, REGISTER["phone_number"])
    assert stored.password_hash != PASSWORD  # hashed, not plain text


def test_register_minimal_fields(client):
    data = {k: REGISTER[k] for k in ("phone_number", "password", "password_confirm")}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 201
    assert response.json()["first_name"] is None


def test_register_duplicate_phone(client):
    client.post("/auth/register", json=REGISTER)
    response = client.post("/auth/register", json=REGISTER)
    assert response.status_code == 409


@pytest.mark.xfail(reason="#11: concurrent duplicate registration -> IntegrityError -> 500")
def test_register_duplicate_phone_race(client, monkeypatch):
    client.post("/auth/register", json=REGISTER)
    # Second request passed the existence check before the first one committed
    monkeypatch.setattr(auth_service, "get_user_by_phone", lambda db, phone: None)
    response = client.post("/auth/register", json=REGISTER)
    assert response.status_code == 409


def test_register_password_mismatch(client):
    response = client.post("/auth/register", json={**REGISTER, "password_confirm": "other123"})
    assert response.status_code == 422


@pytest.mark.parametrize("phone", ["992900000001", "+99290", "+99290000000a", ""])
def test_register_invalid_phone(client, phone):
    response = client.post("/auth/register", json={**REGISTER, "phone_number": phone})
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/auth/register", json={**REGISTER, "password": "123", "password_confirm": "123"})
    assert response.status_code == 422


def test_login(client):
    client.post("/auth/register", json=REGISTER)
    response = login(client, REGISTER["phone_number"])
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client, customer):
    assert login(client, customer.phone_number, "wrong-password").status_code == 401


def test_login_unknown_phone(client):
    assert login(client, "+992999999999").status_code == 401


def test_me(client, customer):
    token = login(client, customer.phone_number).json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == customer.id


def test_me_shows_roles(client, seller):
    assert client.get("/auth/me", headers=auth(seller)).json()["roles"] == ["seller"]


def test_me_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_invalid_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_me_token_of_deleted_user(client, db, customer):
    headers = auth(customer)
    db.delete(customer)
    db.commit()
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_blocked_user_cannot_login(client, make_user):
    user = make_user(is_active=False)
    response = login(client, user.phone_number)
    assert response.status_code == 403


def test_blocked_user_token_rejected(client, db, customer):
    headers = auth(customer)
    customer.is_active = False
    db.commit()
    assert client.get("/auth/me", headers=headers).status_code == 401
