import pytest


def test_seller_updates_store(client, seller_headers):
    response = client.patch("/seller/store", json={"store_name": "TechStore Pro"}, headers=seller_headers)
    assert response.status_code == 200
    assert response.json()["store_name"] == "TechStore Pro"
    assert response.json()["address"] == "Dushanbe"


def test_seller_clears_store_description(client, db, seller, seller_headers):
    seller.seller_profile.store_description = "old"
    db.commit()
    response = client.patch("/seller/store", json={"store_description": None}, headers=seller_headers)
    assert response.status_code == 200
    assert response.json()["store_description"] is None


@pytest.mark.parametrize("field", ["store_name", "address", "phone_number"])
def test_store_required_field_cannot_be_null(client, seller_headers, field):
    assert client.patch("/seller/store", json={field: None}, headers=seller_headers).status_code == 422


def test_courier_updates_profile(client, courier_headers):
    response = client.patch("/courier/profile", json={"transport_type": "car"}, headers=courier_headers)
    assert response.status_code == 200
    assert response.json()["transport_type"] == "car"


@pytest.mark.parametrize("body", [
    {"address": None}, {"phone_number": None}, {"transport_type": None}, {"address": ""},
])
def test_courier_profile_invalid(client, courier_headers, body):
    assert client.patch("/courier/profile", json=body, headers=courier_headers).status_code == 422


def test_category_name_cannot_be_null(client, admin_headers, category):
    response = client.patch(f"/categories/{category.id}", json={"name_ru": None}, headers=admin_headers)
    assert response.status_code == 422
