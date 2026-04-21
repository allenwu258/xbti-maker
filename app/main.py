from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db
from app.web.routes import router as web_router
from app.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="XBTI Maker", version="0.1.0")
    init_db()
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(web_router)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
