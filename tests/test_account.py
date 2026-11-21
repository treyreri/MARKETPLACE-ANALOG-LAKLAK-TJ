from tests.conftest import auth


def test_update_profile(client, customer):
    response = client.patch("/auth/me", json={"first_name": " Madina ", "last_name": "Rahimova"},
                            headers=auth(customer))
    assert response.status_code == 200
    assert (response.json()["first_name"], response.json()["last_name"]) == ("Madina", "Rahimova")


def test_update_profile_partial_and_clear(client, customer):
    client.patch("/auth/me", json={"last_name": "Valiev"}, headers=auth(customer))
    body = client.patch("/auth/me", json={"first_name": ""}, headers=auth(customer)).json()
    assert body["first_name"] is None
    assert body["last_name"] == "Valiev"


def test_update_profile_requires_login(client):
    assert client.patch("/auth/me", json={"first_name": "X"}).status_code == 401


def test_update_profile_too_long(client, customer):
    assert client.patch("/auth/me", json={"first_name": "x" * 51}, headers=auth(customer)).status_code == 422
