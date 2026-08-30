export interface VerifyResult {
  token_audit: string;
  total_debits: number;
  total_credits: number;
  discrepancy: number;
  status: string;
}

export interface CloseResult {
  business_date: string;
  new_business_date: string;
  report_hash: string;
  report_urls: Record<string, string>;
}

export interface DiscrepancyItem {
  folio_id: string;
  booking_id: string;
  type: string;
  balance: number;
}

const BASE = "/api/proxy/night-audit/night-audit";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    const err = new Error(message ?? `Request failed (${response.status})`) as Error & { discrepancy?: number };
    if (detail?.discrepancy !== undefined) err.discrepancy = detail.discrepancy;
    throw err;
  }
  return response.json();
}

export async function fetchBusinessDate(establishmentId: string): Promise<{ business_date: string }> {
  const res = await fetch(`${BASE}/business-date?establishment_id=${establishmentId}`, { cache: "no-store" });
  return handle(res);
}

export async function verifyAudit(establishmentId: string, businessDate: string): Promise<VerifyResult> {
  const res = await fetch(`${BASE}/verify`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ establishment_id: establishmentId, business_date: businessDate }),
  });
  return handle<VerifyResult>(res);
}

export async function fetchDiscrepancyReport(
  establishmentId: string,
  businessDate: string
): Promise<DiscrepancyItem[]> {
  const res = await fetch(`${BASE}/discrepancy-report?establishment_id=${establishmentId}&date=${businessDate}`, {
    cache: "no-store",
  });
  return handle<DiscrepancyItem[]>(res);
}

export function reportDownloadUrl(establishmentId: string, businessDate: string, filename: string): string {
  return `${BASE}/reports/${establishmentId}/${businessDate}/${encodeURIComponent(filename)}`;
}

export async function closeAudit(
  establishmentId: string,
  businessDate: string,
  auditToken: string
): Promise<CloseResult> {
  const res = await fetch(`${BASE}/close`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-audit-token": auditToken },
    body: JSON.stringify({ establishment_id: establishmentId, business_date: businessDate }),
  });
  return handle<CloseResult>(res);
}
