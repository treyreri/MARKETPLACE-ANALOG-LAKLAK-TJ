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


@router.get("/product/{product_id}", response_class=HTMLResponse)
def product(request: Request, product_id: int):
    return render(request, "product.html", "product", product_id=product_id)


@router.get("/shopping-cart", response_class=HTMLResponse)
def shopping_cart(request: Request):
    return render(request, "cart.html", "cart")


@router.get("/catalog", response_class=HTMLResponse)
def catalog(request: Request):
    return render(request, "catalog.html", "catalog")


def app_page(path: str, script: str, page: str, kind: str | None = None) -> None:
    """Register a JS-rendered page that uses the generic app.html shell."""
    def view(request: Request):
        return render(request, "app.html", page, script=script, kind=kind)
    router.add_api_route(path, view, methods=["GET"], response_class=HTMLResponse)


# Linked from the layout but not built yet: a friendly placeholder instead of 404
COMING_SOON = [
    "/about", "/contact",
]


def _coming_soon(request: Request):
    return render(request, "coming_soon.html", "coming-soon")


for _path in COMING_SOON:
    router.add_api_route(_path, _coming_soon, methods=["GET"], response_class=HTMLResponse)


app_page("/account/orders", "orders.js", "orders")
app_page("/account", "account.js", "account")
app_page("/become-seller", "apply.js", "apply", kind="seller")
app_page("/become-courier", "apply.js", "apply", kind="courier")
app_page("/application/seller", "application.js", "application", kind="seller")
app_page("/application/courier", "application.js", "application", kind="courier")
app_page("/seller/login", "role_login.js", "role-login", kind="seller")
app_page("/courier/login", "role_login.js", "role-login", kind="courier")
app_page("/dashboard/seller", "seller.js", "seller-dashboard")
