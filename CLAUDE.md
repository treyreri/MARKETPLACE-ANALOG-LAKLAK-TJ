# Pixel Unicorn Marketplace

Educational marketplace. Full spec: `docs/Pixel_Unicorn_TZ.md` (Russian) — source of truth for requirements.

## Stack
- Backend: FastAPI, SQLAlchemy 2.0 (typed `Mapped`), Pydantic v2, Alembic, SQLite
- Auth: JWT (PyJWT) via `HTTPBearer`; passwords hashed with pwdlib (argon2)
- Dev environment: Windows, cmd terminal, virtualenv `.venv`

## Architecture
- `app/models` — SQLAlchemy models; all imported in `app/models/__init__.py`
- `app/schemas` — Pydantic schemas
- `app/services` — business logic. Services know nothing about HTTP; they raise their own exceptions
- `app/routers` — HTTP only: call services, map exceptions to `HTTPException`
- `app/dependencies` — `DbSession`, `CurrentUser`, `AdminUser`, `SellerUser`, `CourierUser`, `CurrentLanguage`
- `app/scripts` — CLI: `create_admin`, `grant_role`, `seed_categories`

## Key decisions (do not change without asking me)
- Roles live in `user_roles` table (seller / courier / admin). Customer = any registered user.
- Applications (`SellerApplication`, `CourierApplication`, shared `ApplicationMixin`) are separate from profiles (`SellerProfile`, `CourierProfile`).
- Checkout is atomic: conditional `UPDATE products SET quantity = quantity - n WHERE quantity >= n`, single transaction.
- `OrderItem` stores a product snapshot: `product_name`, `price`, `seller_id`. `product_id` is nullable.
- Status transitions are defined in dicts `ALLOWED_TRANSITIONS` (order) and `NEXT_DELIVERY_STATUS` (delivery). When a courier is assigned, only the courier sets shipped/delivered.
- Someone else's resource → 404, not 403.
- SQLite: `PRAGMA foreign_keys=ON`, Unicode `lower()` via `create_function`, Alembic `render_as_batch=True`, constraint naming convention.

## Working rules
- Commit messages in English, Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `style:`). Small atomic commits: one logical change per commit.
- Before every commit: `pytest` passes; `alembic check` is clean.
- Model changes → `alembic revision --autogenerate`, then review the generated file manually.
- Never `git push`. Never rewrite history (`rebase`, `--amend` on existing commits).
- Never commit `.env`, `*.db`, `.venv/`, `uploads/*`.
- Code, comments, API messages: English. Reports and explanations to me: Russian.
- This is a learning project: after each phase, briefly explain what was done and why, especially non-obvious decisions.
- If a requirement is ambiguous or a decision is hard to reverse — ask, don't guess.
