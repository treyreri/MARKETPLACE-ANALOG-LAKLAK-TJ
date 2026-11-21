from fastapi import FastAPI
from app.config import settings

app = FastAPI(title = settings.app_name)

@app.get("/health")
def health_check():
    return {"status" : "ok"}

from app.routers import auth
app.include_router(auth.router)

from app.routers import auth, categories
app.include_router(auth.router)
app.include_router(categories.router)


from fastapi.staticfiles import StaticFiles
from app.routers import auth, categories, products, seller

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(seller.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from app.routers import admin, auth, categories, products, seller
app.include_router(admin.router)

from app.routers import admin, auth, categories, courier, products, seller
app.include_router(courier.router)


from app.routers import admin, auth, cart, categories, courier, products, seller
app.include_router(cart.router)

from app.routers import admin, auth, cart, categories, courier, orders, products, seller
app.include_router(orders.router)