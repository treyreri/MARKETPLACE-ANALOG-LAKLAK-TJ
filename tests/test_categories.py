import pytest

from app.models import Category


def test_list_categories_default_russian(client, category):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Электроника"


def test_list_categories_lang_en(client, category):
    item = client.get("/categories?lang=en").json()[0]
    assert item["name"] == "Electronics"
    assert item["name_ru"] == "Электроника"
    assert item["name_en"] == "Electronics"


def test_accept_language_header(client, category):
    response = client.get("/categories", headers={"Accept-Language": "en-US,en;q=0.9"})
    assert response.json()[0]["name"] == "Electronics"


def test_lang_param_overrides_header(client, category):
    response = client.get("/categories?lang=ru", headers={"Accept-Language": "en"})
    assert response.json()[0]["name"] == "Электроника"


def test_unsupported_lang(client):
    assert client.get("/categories?lang=de").status_code == 422


def test_get_category(client, category):
    response = client.get(f"/categories/{category.id}?lang=en")
    assert response.status_code == 200
    assert response.json()["name"] == "Electronics"


def test_get_missing_category(client):
    assert client.get("/categories/999").status_code == 404


def test_create_category(client, admin_headers):
    body = {"name_ru": "Книги", "name_en": "Books", "description": "Paper and e-books"}
    response = client.post("/categories?lang=en", json=body, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Books"
    assert response.json()["description"] == "Paper and e-books"


@pytest.mark.parametrize("body", [
    {"name_ru": "Электроника", "name_en": "Other"},
    {"name_ru": "Другое", "name_en": "Electronics"},
])
def test_create_category_duplicate_name(client, admin_headers, category, body):
    assert client.post("/categories", json=body, headers=admin_headers).status_code == 409


def test_create_category_empty_name(client, admin_headers):
    body = {"name_ru": "", "name_en": "Books"}
    assert client.post("/categories", json=body, headers=admin_headers).status_code == 422


def test_update_category(client, db, admin_headers, category):
    response = client.patch(
        f"/categories/{category.id}", json={"name_en": "Gadgets"}, headers=admin_headers)
    assert response.status_code == 200
    db.refresh(category)
    assert category.name_en == "Gadgets"
    assert category.name_ru == "Электроника"  # untouched


def test_update_category_keep_own_name(client, admin_headers, category):
    body = {"name_ru": "Электроника", "name_en": "Electronics"}
    response = client.patch(f"/categories/{category.id}", json=body, headers=admin_headers)
    assert response.status_code == 200


def test_update_category_name_taken(client, db, admin_headers, category):
    db.add(Category(name_ru="Книги", name_en="Books"))
    db.commit()
    response = client.patch(
        f"/categories/{category.id}", json={"name_en": "Books"}, headers=admin_headers)
    assert response.status_code == 409


def test_update_missing_category(client, admin_headers):
    response = client.patch("/categories/999", json={"name_en": "X"}, headers=admin_headers)
    assert response.status_code == 404


def test_update_category_clear_description(client, db, admin_headers):
    category = Category(name_ru="Книги", name_en="Books", description="old")
    db.add(category)
    db.commit()
    client.patch(f"/categories/{category.id}", json={"description": None}, headers=admin_headers)
    db.refresh(category)
    assert category.description is None


def test_delete_empty_category(client, db, admin_headers, category):
    category_id = category.id
    response = client.delete(f"/categories/{category_id}", headers=admin_headers)
    assert response.status_code == 204
    db.expire_all()
    assert db.get(Category, category_id) is None


def test_cannot_delete_category_with_products(client, db, admin_headers, product, category):
    response = client.delete(f"/categories/{category.id}", headers=admin_headers)
    assert response.status_code == 409
    db.expire_all()
    assert db.get(Category, category.id) is not None


def test_delete_missing_category(client, admin_headers):
    assert client.delete("/categories/999", headers=admin_headers).status_code == 404
