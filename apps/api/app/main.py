from fastapi import FastAPI

from .api.routes.health import router as health_router
from .api.routes.sentinel import router as sentinel_router
from .core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(sentinel_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
