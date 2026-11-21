from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import admin, auth, cart, categories, courier, orders, products, seller
from app.utils.files import UPLOAD_ROOT
from app.web import pages
from app.web.pages import APP_DIR

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {"status": "ok"}


for router in (auth, categories, products, seller, courier, cart, orders, admin):
    app.include_router(router.router)

app.include_router(pages.router)

UPLOAD_ROOT.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
