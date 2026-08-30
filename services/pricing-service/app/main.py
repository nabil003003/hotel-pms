from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import pricing_router, rates_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.service_name, version="0.1.0")

Instrumentator(excluded_handlers=["/healthz", "/metrics"]).instrument(
    app, metric_namespace="pms", metric_subsystem="api"
).expose(app, endpoint="/metrics", include_in_schema=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pricing_router)
app.include_router(rates_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
