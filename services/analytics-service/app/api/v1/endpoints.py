import json
import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import CurrentUser, assert_path_establishment_access, get_db, require_roles, require_super_admin
from app.domain.services import (
    get_channel_performance,
    get_kpi_consolidated,
    get_kpi_monthly,
    get_kpi_today,
    get_occupancy_forecast,
    get_segments_distribution,
    get_segments_revenue,
    get_segments_trend,
    get_ytd_compare,
)
from app.infrastructure import redis_client as cache

from .schemas import (
    ChannelPerformanceOut,
    KpiConsolidatedOut,
    KpiMonthlyOut,
    KpiTodayOut,
    OccupancyForecastOut,
    SegmentDistributionOut,
    SegmentRevenueOut,
    SegmentTrendOut,
    YtdCompareOut,
)

settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["analytics"])

READ_ROLES = ("manager", "admin", "comptable")


@router.get("/kpi/today", response_model=KpiTodayOut)
async def kpi_today(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> KpiTodayOut:
    assert_path_establishment_access(user, establishment_id)
    cache_key = f"kpi:today:{establishment_id}"
    cached = await cache.cache_get(cache_key)
    if cached:
        return KpiTodayOut.model_validate(json.loads(cached))
    result = await get_kpi_today(db, establishment_id)
    await cache.cache_set(cache_key, json.dumps(result, default=str), settings.kpi_today_cache_seconds)
    return KpiTodayOut.model_validate(result)


@router.get("/kpi/monthly", response_model=KpiMonthlyOut)
async def kpi_monthly(
    establishment_id: uuid.UUID,
    month: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> KpiMonthlyOut:
    assert_path_establishment_access(user, establishment_id)
    year_i, month_i = (int(p) for p in month.split("-"))
    cache_key = f"kpi:monthly:{establishment_id}:{month}"
    cached = await cache.cache_get(cache_key)
    if cached:
        return KpiMonthlyOut.model_validate(json.loads(cached))
    result = await get_kpi_monthly(db, establishment_id, year_i, month_i)
    await cache.cache_set(cache_key, json.dumps(result, default=str), settings.kpi_monthly_cache_seconds)
    return KpiMonthlyOut.model_validate(result)


@router.get("/kpi/consolidated", response_model=KpiConsolidatedOut)
async def kpi_consolidated(
    month: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> KpiConsolidatedOut:
    year_i, month_i = (int(p) for p in month.split("-"))
    result = await get_kpi_consolidated(db, year_i, month_i)
    return KpiConsolidatedOut.model_validate(result)


@router.get("/segments/distribution", response_model=SegmentDistributionOut)
async def segments_distribution(
    establishment_id: uuid.UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> SegmentDistributionOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_segments_distribution(db, establishment_id, period)
    return SegmentDistributionOut.model_validate(result)


@router.get("/segments/revenue", response_model=SegmentRevenueOut)
async def segments_revenue(
    establishment_id: uuid.UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> SegmentRevenueOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_segments_revenue(db, establishment_id, period)
    return SegmentRevenueOut.model_validate(result)


@router.get("/segments/trend", response_model=SegmentTrendOut)
async def segments_trend(
    establishment_id: uuid.UUID,
    segment: str,
    granularity: str = "month",
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> SegmentTrendOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_segments_trend(db, establishment_id, segment)
    return SegmentTrendOut.model_validate(result)


@router.get("/ytd/compare", response_model=YtdCompareOut)
async def ytd_compare(
    establishment_id: uuid.UUID,
    month: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> YtdCompareOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_ytd_compare(db, establishment_id, date_type.today().year, month)
    return YtdCompareOut.model_validate(result)


@router.get("/channel/performance", response_model=ChannelPerformanceOut)
async def channel_performance(
    establishment_id: uuid.UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> ChannelPerformanceOut:
    """Vue analytics — distincte de channel-manager-service's `/performance`
    (Sprint 2, `sync_logs`), voir docstring de `get_channel_performance`."""
    assert_path_establishment_access(user, establishment_id)
    result = await get_channel_performance(db, establishment_id, period)
    return ChannelPerformanceOut.model_validate(result)


@router.get("/forecast/occupancy", response_model=OccupancyForecastOut)
async def forecast_occupancy(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*READ_ROLES)),
) -> OccupancyForecastOut:
    """Rapport `occupancy_forecast_J+1.pdf` (night-audit-service, D12)."""
    assert_path_establishment_access(user, establishment_id)
    result = await get_occupancy_forecast(db, establishment_id, date)
    return OccupancyForecastOut.model_validate(result)
