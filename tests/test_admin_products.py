from app.models import Product
from tests.conftest import auth


def test_list_includes_hidden_and_blocked_sellers(client, admin_headers, make_product, make_seller, seller, category):
    make_product(seller, category, name="Visible")
    make_product(seller, category, name="Hidden", is_active=False)
    blocked = make_seller(store_name="Blocked", is_active=False)
    make_product(blocked, category, name="Blocked seller item")
    assert client.get("/admin/products", headers=admin_headers).json()["total"] == 3
    assert client.get("/products").json()["total"] == 1


def test_filter_by_seller_and_status(client, admin_headers, make_product, make_seller, seller, category):
    make_product(seller, category, name="Mine")
    make_product(seller, category, name="Mine hidden", is_active=False)
    make_product(make_seller(store_name="Other"), category, name="Theirs")
    by_seller = client.get("/admin/products", params={"seller_id": seller.id}, headers=admin_headers).json()
    assert by_seller["total"] == 2
    hidden = client.get("/admin/products", params={"is_active": False}, headers=admin_headers).json()
    assert [p["name"] for p in hidden["items"]] == ["Mine hidden"]


def test_hide_and_show(client, admin_headers, product):
    response = client.patch(f"/admin/products/{product.id}", json={"is_active": False}, headers=admin_headers)
    assert response.status_code == 200 and response.json()["is_active"] is False
    assert client.get(f"/products/{product.id}").status_code == 404
    client.patch(f"/admin/products/{product.id}", json={"is_active": True}, headers=admin_headers)
    assert client.get(f"/products/{product.id}").status_code == 200


def test_admin_edits_product(client, admin_headers, product):
    response = client.patch(f"/admin/products/{product.id}", json={"name": "Fixed name"}, headers=admin_headers)
    assert response.json()["name"] == "Fixed name"


def test_is_active_cannot_be_null(client, admin_headers, product):
    response = client.patch(f"/admin/products/{product.id}", json={"is_active": None}, headers=admin_headers)
    assert response.status_code == 422


def test_seller_cannot_toggle_visibility(client, db, seller_headers, product):
    client.patch(f"/seller/products/{product.id}", json={"is_active": False}, headers=seller_headers)
    db.refresh(product)
    assert product.is_active is True


def test_admin_deletes_product(client, db, admin_headers, product):
    product_id = product.id
    assert client.delete(f"/admin/products/{product_id}", headers=admin_headers).status_code == 204
    db.expire_all()
    assert db.get(Product, product_id) is None


def test_missing_product(client, admin_headers):
    assert client.get("/admin/products/999", headers=admin_headers).status_code == 404
    assert client.delete("/admin/products/999", headers=admin_headers).status_code == 404


def test_admin_only(client, seller, product):
    assert client.get("/admin/products", headers=auth(seller)).status_code == 403
