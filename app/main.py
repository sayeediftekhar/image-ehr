from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import get_settings
from app.routers import auth, dashboard

def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(title=cfg.APP_NAME)

    # Add middleware
    app.add_middleware(SessionMiddleware, secret_key=cfg.SECRET_KEY)

    # Mount static files BEFORE including routers
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include routers
    app.include_router(auth.router)
    app.include_router(dashboard.router)

    return app

app = create_app()