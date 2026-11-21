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