from app.models import Category


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_fixtures_share_database(client, category):
    response = client.get("/categories")
    assert [c["id"] for c in response.json()] == [category.id]


def test_sqlite_foreign_keys_enabled(db):
    assert db.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_sqlite_unicode_lower(db):
    db.add(Category(name_ru="ЭЛЕКТРОНИКА", name_en="X"))
    db.commit()
    assert db.connection().exec_driver_sql("SELECT lower(name_ru) FROM categories").scalar() == "электроника"
