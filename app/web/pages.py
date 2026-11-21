"""HTML page routes. Pages are thin shells: data comes from the JSON API via JS."""
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
