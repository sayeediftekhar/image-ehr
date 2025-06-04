from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import get_settings

def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(title=cfg.APP_NAME)

    app.add_middleware(SessionMiddleware, secret_key=cfg.SECRET_KEY)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include NEW modular routers FIRST
    from app.routers import auth, dashboard, health, admin, billing, patients, visits
    
    app.include_router(patients.router)  # Make sure this comes first
#    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(health.router)
    app.include_router(admin.router)
    app.include_router(billing.router)
    app.include_router(visits.router)

    
    return app

app = create_app()