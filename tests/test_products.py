import io
import struct
import zlib
from decimal import Decimal

import pytest

from PIL import Image

from app.models import Category, Product
from tests.conftest import auth


def png_bytes() -> bytes:
    """A valid 1x1 PNG."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b""))


def names(response) -> list[str]:
    return [item["name"] for item in response.json()["items"]]


@pytest.fixture
def catalog(db, make_product, seller, category):
    books = Category(name_ru="Книги", name_en="Books")
    db.add(books)
    db.commit()
    make_product(seller, category, name="Беспроводные Наушники", description="Хороший звук",
                 brand="Sony", price=Decimal("250"))
    make_product(seller, category, name="Smart Watch", description="Fitness tracker",
                 price=Decimal("400"))
    make_product(seller, books, name="Мастер и Маргарита", price=Decimal("50"))
    make_product(seller, category, name="Hidden Phone", price=Decimal("100"), is_active=False)
    return {"electronics": category, "books": books}


# public catalog

@pytest.mark.parametrize("query", ["наушники", "НАУШНИКИ", "Наушн", "беспроводные наушники"])
def test_search_cyrillic_case_insensitive(client, catalog, query):
    assert names(client.get("/products/search", params={"q": query})) == ["Беспроводные Наушники"]


@pytest.mark.parametrize("query,expected", [
    ("звук", ["Беспроводные Наушники"]),   # description
    ("sony", ["Беспроводные Наушники"]),   # brand
    ("fitness", ["Smart Watch"]),           # latin description
    ("книги", ["Мастер и Маргарита"]),       # category name ru
    ("books", ["Мастер и Маргарита"]),       # category name en
])
def test_search_fields(client, catalog, query, expected):
    assert names(client.get("/products", params={"q": query})) == expected


def test_search_like_wildcards_escaped(client, catalog):
    assert client.get("/products", params={"q": "%"}).json()["total"] == 0


def test_inactive_products_hidden(client, catalog):
    response = client.get("/products")
    assert "Hidden Phone" not in names(response)
    assert response.json()["total"] == 3


def test_filter_by_category(client, catalog):
    response = client.get("/products", params={"category_id": catalog["books"].id})
    assert names(response) == ["Мастер и Маргарита"]


def test_products_by_category_route(client, catalog):
    response = client.get(f"/products/category/{catalog['books'].id}")
    assert names(response) == ["Мастер и Маргарита"]


def test_filter_by_price_range(client, catalog):
    response = client.get("/products", params={"min_price": 100, "max_price": 300})
    assert names(response) == ["Беспроводные Наушники"]


def test_filter_combined(client, catalog):
    params = {"category_id": catalog["electronics"].id, "min_price": 300, "max_price": 500}
    assert names(client.get("/products", params=params)) == ["Smart Watch"]


def test_min_price_greater_than_max(client):
    assert client.get("/products", params={"min_price": 500, "max_price": 100}).status_code == 422


def test_negative_price_filter(client):
    assert client.get("/products", params={"min_price": -1}).status_code == 422


@pytest.mark.parametrize("sort,expected", [
    ("price_asc", ["Мастер и Маргарита", "Беспроводные Наушники", "Smart Watch"]),
    ("price_desc", ["Smart Watch", "Беспроводные Наушники", "Мастер и Маргарита"]),
    ("newest", ["Мастер и Маргарита", "Smart Watch", "Беспроводные Наушники"]),
])
def test_sort(client, catalog, sort, expected):
    assert names(client.get("/products", params={"sort": sort})) == expected


def test_unknown_sort(client):
    assert client.get("/products", params={"sort": "random"}).status_code == 422


def test_pagination(client, catalog):
    params = {"sort": "price_asc", "limit": 2, "offset": 1}
    body = client.get("/products", params=params).json()
    assert [i["name"] for i in body["items"]] == ["Беспроводные Наушники", "Smart Watch"]
    assert (body["total"], body["limit"], body["offset"]) == (3, 2, 1)


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_pagination_bounds(client, params):
    assert client.get("/products", params=params).status_code == 422


def test_product_detail(client, product):
    response = client.get(f"/products/{product.id}?lang=en")
    assert response.status_code == 200
    body = response.json()
    assert body["price"] == "250.00"
    assert body["category"]["name"] == "Electronics"
    assert body["seller"]["name"] == "TechStore"
    assert body["quantity"] == 5


def test_product_detail_inactive(client, db, product):
    product.is_active = False
    db.commit()
    assert client.get(f"/products/{product.id}").status_code == 404


def test_product_detail_missing(client):
    assert client.get("/products/999").status_code == 404


@pytest.mark.xfail(reason="#18: products of blocked sellers are visible in the catalog")
def test_blocked_seller_products_hidden(client, db, product, seller):
    seller.is_active = False
    db.commit()
    assert client.get("/products").json()["total"] == 0
    assert client.get(f"/products/{product.id}").status_code == 404


# seller management

PRODUCT = {"name": "Phone", "description": "Nice", "brand": "Acme", "price": "199.99", "quantity": 3}


def test_create_product(client, seller_headers, category):
    response = client.post(
        "/seller/products", json={**PRODUCT, "category_id": category.id}, headers=seller_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["price"] == "199.99"
    assert body["is_active"] is True
    assert body["image_url"] is None


def test_create_product_unknown_category(client, seller_headers):
    response = client.post(
        "/seller/products", json={**PRODUCT, "category_id": 999}, headers=seller_headers)
    assert response.status_code == 400


@pytest.mark.parametrize("field,value", [
    ("price", "-1"), ("price", "1.999"), ("quantity", -1), ("name", ""),
])
def test_create_product_invalid(client, seller_headers, category, field, value):
    body = {**PRODUCT, "category_id": category.id, field: value}
    assert client.post("/seller/products", json=body, headers=seller_headers).status_code == 422


def test_seller_lists_only_own_products(client, make_seller, make_product, product, category, seller_headers):
    make_product(make_seller(store_name="Other"), category, name="Foreign")
    response = client.get("/seller/products", headers=seller_headers)
    assert [p["name"] for p in response.json()] == ["Wireless Headphones"]


def test_seller_get_own_product(client, product, seller_headers):
    assert client.get(f"/seller/products/{product.id}", headers=seller_headers).status_code == 200


def test_update_product(client, db, product, seller_headers):
    response = client.patch(
        f"/seller/products/{product.id}", json={"price": "300", "quantity": 7}, headers=seller_headers)
    assert response.status_code == 200
    db.refresh(product)
    assert (product.price, product.quantity, product.name) == (Decimal("300"), 7, "Wireless Headphones")


def test_update_product_unknown_category(client, product, seller_headers):
    response = client.patch(
        f"/seller/products/{product.id}", json={"category_id": 999}, headers=seller_headers)
    assert response.status_code == 400


def test_update_product_clear_optional_field(client, db, product, seller_headers):
    product.brand = "Sony"
    db.commit()
    client.patch(f"/seller/products/{product.id}", json={"brand": None}, headers=seller_headers)
    db.refresh(product)
    assert product.brand is None


def test_update_product_null_required_field(client, product, seller_headers):
    response = client.patch(
        f"/seller/products/{product.id}", json={"name": None}, headers=seller_headers)
    assert response.status_code == 422


def test_delete_product(client, db, product, seller_headers):
    product_id = product.id
    assert client.delete(f"/seller/products/{product_id}", headers=seller_headers).status_code == 204
    db.expire_all()
    assert db.get(Product, product_id) is None


@pytest.mark.parametrize("method,suffix,body", [
    ("GET", "", None),
    ("PATCH", "", {"price": "1"}),
    ("DELETE", "", None),
])
def test_other_sellers_product_is_404(client, db, make_seller, product, method, suffix, body):
    other = auth(make_seller(store_name="Other"))
    response = client.request(method, f"/seller/products/{product.id}{suffix}", json=body, headers=other)
    assert response.status_code == 404
    db.refresh(product)
    assert product.price == Decimal("250.00")


def test_other_sellers_product_image_is_404(client, make_seller, product):
    files = {"file": ("a.png", png_bytes(), "image/png")}
    response = client.post(f"/seller/products/{product.id}/image", files=files,
                           headers=auth(make_seller(store_name="Other")))
    assert response.status_code == 404


# images

def test_upload_image(client, product, seller_headers, image_dir):
    files = {"file": ("photo.png", png_bytes(), "image/png")}
    response = client.post(f"/seller/products/{product.id}/image", files=files, headers=seller_headers)
    assert response.status_code == 200
    assert response.json()["image_url"].endswith(".png")
    saved = list(image_dir.iterdir())
    assert len(saved) == 1 and saved[0].name != "photo.png"  # UUID name, not client's


def test_replace_image_deletes_old_file(client, product, seller_headers, image_dir):
    url = f"/seller/products/{product.id}/image"
    for _ in range(2):
        client.post(url, files={"file": ("p.png", png_bytes(), "image/png")}, headers=seller_headers)
    assert len(list(image_dir.iterdir())) == 1


def test_upload_rejects_non_image_content_type(client, product, seller_headers):
    files = {"file": ("a.txt", b"hello", "text/plain")}
    response = client.post(f"/seller/products/{product.id}/image", files=files, headers=seller_headers)
    assert response.status_code == 400


def test_upload_rejects_too_large(client, product, seller_headers):
    files = {"file": ("big.png", b"0" * (5 * 1024 * 1024 + 1), "image/png")}
    response = client.post(f"/seller/products/{product.id}/image", files=files, headers=seller_headers)
    assert response.status_code == 400


def test_upload_rejects_fake_image(client, product, seller_headers, image_dir):
    files = {"file": ("x.png", b"<html><script>alert(1)</script></html>", "image/png")}
    response = client.post(f"/seller/products/{product.id}/image", files=files, headers=seller_headers)
    assert response.status_code == 400
    assert not image_dir.exists() or not list(image_dir.iterdir())


def image_bytes(image_format: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), (112, 201, 177)).save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.mark.parametrize("image_format,extension", [("JPEG", ".jpg"), ("PNG", ".png"), ("WEBP", ".webp")])
def test_upload_allowed_formats(client, product, seller_headers, image_format, extension):
    # Wrong client content_type on purpose: the detected format decides
    files = {"file": ("photo.bin", image_bytes(image_format), "application/octet-stream")}
    response = client.post(f"/seller/products/{product.id}/image", files=files, headers=seller_headers)
    assert response.status_code == 200
    assert response.json()["image_url"].endswith(extension)


@pytest.mark.parametrize("content", [
    image_bytes("GIF"),          # real image, but not an allowed format
    png_bytes()[:40],            # truncated PNG
    png_bytes()[:8] + b"0" * 100,  # PNG signature followed by garbage
])
def test_upload_rejects_invalid_images(client, product, seller_headers, image_dir, content):
    files = {"file": ("x.png", content, "image/png")}
    response = client.post(f"/seller/products/{product.id}/image", files=files, headers=seller_headers)
    assert response.status_code == 400
    assert not image_dir.exists() or not list(image_dir.iterdir())
