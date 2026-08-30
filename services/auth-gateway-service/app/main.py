import asyncio

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as auth_router
from app.config import get_settings
from app.infrastructure.audit_poller import run_audit_poller

settings = get_settings()

app = FastAPI(title="auth-gateway-service", version="0.1.0")


@app.on_event("startup")
async def _start_audit_poller() -> None:
    app.state.audit_poller_task = asyncio.create_task(run_audit_poller())


@app.on_event("shutdown")
async def _stop_audit_poller() -> None:
    task = getattr(app.state, "audit_poller_task", None)
    if task:
        task.cancel()

# Sprint 8 (D15) : métriques Prometheus réelles, pas une config vide —
# noms rapprochés du spec §6.7 (pms_api_*) via metric_namespace/subsystem.
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

app.include_router(auth_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
