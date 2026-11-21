# Treyreri Unicorn Store

Educational marketplace: customers, sellers, couriers and admins.
FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic + SQLite; Jinja2 + vanilla JS frontend.
Spec: [docs/Pixel_Unicorn_TZ.md](docs/Pixel_Unicorn_TZ.md).

## Setup (Windows, cmd)

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `.env` and set `SECRET_KEY` (required, at least 32 characters):

```cmd
python -c "import secrets; print(secrets.token_hex(32))"
```

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./pixel_unicorn.db` | SQLAlchemy URL |
| `SECRET_KEY` | — (required) | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT lifetime |

## Database

```cmd
alembic upgrade head
python -m app.scripts.seed_categories
```

After changing models: `alembic revision --autogenerate -m "..."`, review the file, then `alembic upgrade head`. `alembic check` must be clean.

## Demo data

```cmd
python -m app.scripts.seed_demo_data
```

Safe to run repeatedly. Creates the 10 categories, 3 approved sellers, 50 products with placeholder images (in `uploads/products/`), a courier, a customer and 7 orders in all statuses.

Demo accounts — **local development only**, password for all: `demo12345`

| Role | Phone |
|---|---|
| Admin | `+992900100000` |
| Customer | `+992900100001` |
| Courier | `+992900100002` |
| Seller — TechStore | `+992900100011` |
| Seller — Beauty Corner | `+992900100012` |
| Seller — Happy Kids | `+992900100013` |

## Other scripts

```cmd
python -m app.scripts.create_admin +992900000000 secret123
python -m app.scripts.grant_role +992900000000 seller
```

## Run

```cmd
uvicorn app.main:app --reload
```

- Site: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

## Tests

```cmd
pytest
```

Tests use a temporary SQLite file and never touch `pixel_unicorn.db` or `uploads/`.

## Pages

| Page | URL |
|---|---|
| Home, catalog, product | `/`, `/catalog`, `/product/{id}` |
| Login, register | `/login`, `/register` |
| Cart and checkout | `/shopping-cart` |
| Profile, my orders | `/account`, `/account/orders` |
| Become a seller / courier | `/seller/apply`, `/courier/apply` |
| Seller / Courier Login (spec §17) | `/seller/login`, `/courier/login` |
| Application status | `/application/seller`, `/application/courier` |
| Seller dashboard | `/dashboard/seller` |
| Courier dashboard | `/dashboard/courier` |
| Admin panel | `/admin` |
| About, Contact, Terms | `/about`, `/contact`, `/terms` |

`/cart` and `/orders` are JSON API paths, so the pages use `/shopping-cart` and `/account/orders`.

## TODO

- #22 Move repeated `try/except → HTTPException` in routers to global exception handlers (plan needs approval).
