from sqlalchemy import select
import app.models  # noqa: F401
from app.database import SessionLocal
from app.models.category import Category

CATEGORIES = [
    ("Электроника", "Electronics"),
    ("Спорт и отдых", "Sports & Recreation"),
    ("Красота и уход", "Beauty & Care"),
    ("Дом и интерьер", "Home & Interior"),
    ("Одежда", "Clothing"),
    ("Обувь", "Shoes"),
    ("Аксессуары", "Accessories"),
    ("Книги", "Books"),
    ("Детские товары", "Kids"),
    ("Автомобили и аксессуары", "Cars & Accessories"), ]


def main():
    with SessionLocal() as db:
        existing = set(db.scalars(select(Category.name_en)))
        created = 0
        for name_ru, name_en in CATEGORIES:
            if name_en not in existing:
                db.add(Category(name_ru=name_ru, name_en=name_en))
                created += 1
        db.commit()
        print(f"Created: {created}, skipped: {len(CATEGORIES) - created}")


if __name__ == "__main__":
    main()