import uuid

from pydantic import BaseModel


class KpiTodayOut(BaseModel):
    establishment_id: uuid.UUID
    occupancy_rate: float
    adr: float
    revpar: float
    ca_total: float
    encaissements_total: float
    compare_n1: dict | None
    compare_last_month: dict | None


class KpiMonthlyOut(BaseModel):
    establishment_id: uuid.UUID
    period: str
    occupancy_rate: float
    adr: float
    revpar: float
    dms: float
    ca_total: float
    compare_n1: dict | None


class KpiConsolidatedOut(BaseModel):
    period: str
    nuitees: int
    ca_total: float


class SegmentDistributionItem(BaseModel):
    segment_id: uuid.UUID
    label: str
    nuitees: int
    pct_volume: float


class SegmentDistributionOut(BaseModel):
    segments: list[SegmentDistributionItem]


class SegmentRevenueItem(BaseModel):
    segment_id: uuid.UUID
    label: str
    ca_brut: float


class SegmentRevenueOut(BaseModel):
    segments: list[SegmentRevenueItem]


class SegmentTrendItem(BaseModel):
    period: str
    to: float
    adr: float
    revpar: float


class SegmentTrendOut(BaseModel):
    data: list[SegmentTrendItem]


class YtdCompareOut(BaseModel):
    current_year: dict
    previous_year: dict
    deltas: dict


class ChannelPerformanceItem(BaseModel):
    channel: str
    bookings_count: int
    revenue: float
    commission: float
    net_revenue: float


class ChannelPerformanceOut(BaseModel):
    channels: list[ChannelPerformanceItem]


class OccupancyForecastOut(BaseModel):
    establishment_id: uuid.UUID
    business_date: str
    arrivals_count: int
    projected_occupancy_rate: float
    adr_proxy: float
    revpar_proxy: float
