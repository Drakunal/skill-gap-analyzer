from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings

def create_app():
    app = FastAPI(title="Skill Gap Analyzer (compact)")
    app.include_router(router, prefix="/api/v1")
    return app

app = create_app()
