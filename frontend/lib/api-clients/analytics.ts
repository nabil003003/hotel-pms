export interface KpiToday {
  establishment_id: string;
  occupancy_rate: number;
  adr: number;
  revpar: number;
  ca_total: number;
  encaissements_total: number;
}

export interface KpiMonthly {
  establishment_id: string;
  period: string;
  occupancy_rate: number;
  adr: number;
  revpar: number;
  dms: number;
  ca_total: number;
}

export interface SegmentDistributionItem {
  segment_id: string;
  label: string;
  nuitees: number;
  pct_volume: number;
}

const BASE = "/api/proxy/analytics";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchKpiToday(establishmentId: string): Promise<KpiToday> {
  const res = await fetch(`${BASE}/kpi/today?establishment_id=${establishmentId}`, { cache: "no-store" });
  return handle<KpiToday>(res);
}

export async function fetchKpiMonthly(establishmentId: string, month: string): Promise<KpiMonthly> {
  const res = await fetch(`${BASE}/kpi/monthly?establishment_id=${establishmentId}&month=${month}`, {
    cache: "no-store",
  });
  return handle<KpiMonthly>(res);
}

export async function fetchSegmentsDistribution(
  establishmentId: string,
  period: string
): Promise<{ segments: SegmentDistributionItem[] }> {
  const res = await fetch(`${BASE}/segments/distribution?establishment_id=${establishmentId}&period=${period}`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function fetchSegmentsRevenue(
  establishmentId: string,
  period: string
): Promise<{ segments: { segment_id: string; label: string; ca_brut: number }[] }> {
  const res = await fetch(`${BASE}/segments/revenue?establishment_id=${establishmentId}&period=${period}`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function fetchSegmentsTrend(
  establishmentId: string,
  segment: string
): Promise<{ data: { period: string; to: number; adr: number; revpar: number }[] }> {
  const res = await fetch(`${BASE}/segments/trend?establishment_id=${establishmentId}&segment=${segment}`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function fetchYtdCompare(
  establishmentId: string,
  month: number
): Promise<{
  current_year: { to: number; adr: number; ca: number };
  previous_year: { to: number; adr: number; ca: number };
  deltas: { to_pct: number; adr_pct: number; ca_pct: number };
}> {
  const res = await fetch(`${BASE}/ytd/compare?establishment_id=${establishmentId}&month=${month}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchChannelPerformance(
  establishmentId: string,
  period: string
): Promise<{ channels: { channel: string; bookings_count: number; revenue: number; commission: number; net_revenue: number }[] }> {
  const res = await fetch(`${BASE}/channel/performance?establishment_id=${establishmentId}&period=${period}`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function fetchKpiConsolidated(month: string): Promise<{ period: string; nuitees: number; ca_total: number }> {
  const res = await fetch(`${BASE}/kpi/consolidated?month=${month}`, { cache: "no-store" });
  return handle(res);
}
