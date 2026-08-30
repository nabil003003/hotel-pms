import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import bookings_router, customers_router, planning_router, segments_router, ws_router
from app.config import get_settings
from app.domain.services import expire_stale_options
from app.events.consumer import run_consumer_forever
from app.infrastructure.database import AsyncSessionLocal

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_option_expiry_forever() -> None:
    """Pas de Celery réel (non-goal Sprint 3) — boucle asyncio en tâche de
    fond, même stratégie que les consumers RabbitMQ existants."""
    while True:
        await asyncio.sleep(settings.option_expiry_poll_seconds)
        try:
            async with AsyncSessionLocal() as db:
                expired = await expire_stale_options(db)
                if expired:
                    logger.info("expired %d stale booking option(s)", expired)
        except Exception:  # noqa: BLE001
            logger.exception("option-expiry loop iteration failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = asyncio.create_task(run_consumer_forever())
    expiry_task = asyncio.create_task(run_option_expiry_forever())
    yield
    for task in (consumer_task, expiry_task):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title=settings.service_name, version="0.1.0", lifespan=lifespan)

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

app.include_router(segments_router)
app.include_router(customers_router)
app.include_router(bookings_router)
app.include_router(planning_router)
app.include_router(ws_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
