"""HTML page routes. Pages are thin shells: data comes from the JSON API via JS.

Page paths must not collide with API paths (GET /cart and GET /orders are
JSON endpoints), hence /shopping-cart and /account/orders.
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=APP_DIR / "templates")

router = APIRouter(include_in_schema=False)


def render(request: Request, template: str, page: str, **context) -> HTMLResponse:
    return templates.TemplateResponse(request, template, {"page": page, **context})


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "index.html", "home")


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return render(request, "login.html", "login")


@router.get("/register", response_class=HTMLResponse)
def register(request: Request):
    return render(request, "register.html", "register")


# Linked from the layout but not built yet: a friendly placeholder instead of 404
COMING_SOON = [
    "/catalog", "/product/{product_id}", "/shopping-cart",
    "/account/orders", "/about", "/contact",
    "/become-seller", "/seller/login", "/become-courier", "/courier/login",
]


def _coming_soon(request: Request):
    return render(request, "coming_soon.html", "coming-soon")


for _path in COMING_SOON:
    router.add_api_route(_path, _coming_soon, methods=["GET"], response_class=HTMLResponse)
