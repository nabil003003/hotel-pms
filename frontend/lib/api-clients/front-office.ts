export interface Folio {
  id: string;
  establishment_id: string;
  booking_id: string;
  type: "A" | "B";
  status: "open" | "closed";
  third_party_ref: string | null;
  total_charges: number;
  total_payments: number;
  balance: number;
  opened_at: string;
  closed_at: string | null;
  business_date: string;
  version: number;
}

export interface Charge {
  id: string;
  folio_id: string;
  poste_comptable: string;
  libelle: string;
  quantity: number;
  unit_price_ht: number;
  montant_ht: number;
  tva_rate: number;
  tva_amount: number;
  montant_ttc: number;
  source_service: string | null;
  created_at: string;
}

export interface Payment {
  id: string;
  folio_id: string;
  mode: string;
  montant: number;
  reference: string | null;
  encaisse_at: string;
}

const BASE = "/api/proxy/front-office";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function checkIn(establishmentId: string, bookingId: string): Promise<{ booking_id: string; folio_ids: string[] }> {
  const res = await fetch(`${BASE}/folios/check-in`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ establishment_id: establishmentId, booking_id: bookingId }),
  });
  return handle(res);
}

export async function checkOut(establishmentId: string, bookingId: string): Promise<{ booking_id: string; folio_ids: string[] }> {
  const res = await fetch(`${BASE}/folios/check-out`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ establishment_id: establishmentId, booking_id: bookingId }),
  });
  return handle(res);
}

export async function fetchFoliosForBooking(bookingId: string): Promise<Folio[]> {
  const res = await fetch(`${BASE}/folios?booking_id=${bookingId}`, { cache: "no-store" });
  return handle<Folio[]>(res);
}

export async function addCharge(
  folioId: string,
  input: {
    poste_comptable: string;
    libelle: string;
    quantity: number;
    unit_price_ht?: number;
    catalog_item_id?: string;
  }
): Promise<Charge> {
  const res = await fetch(`${BASE}/folios/${folioId}/charges`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Charge>(res);
}

export async function addPayment(
  folioId: string,
  input: { mode: string; montant: number; reference?: string }
): Promise<Payment> {
  const res = await fetch(`${BASE}/folios/${folioId}/payments`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Payment>(res);
}

// -------------------------------------------------------------- reports ---

export async function fetchDailyDebits(establishmentId: string, date: string): Promise<{ business_date: string; total_debits: number }> {
  const res = await fetch(`${BASE}/folios/reports/daily-debits?establishment_id=${establishmentId}&date=${date}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchDailyCredits(establishmentId: string, date: string): Promise<{ business_date: string; total_credits: number }> {
  const res = await fetch(`${BASE}/folios/reports/daily-credits?establishment_id=${establishmentId}&date=${date}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchDailyCaDetail(
  establishmentId: string,
  date: string
): Promise<{ business_date: string; lines: { poste_comptable: string; montant_ht: number; tva_amount: number; montant_ttc: number }[] }> {
  const res = await fetch(`${BASE}/folios/reports/daily-ca-detail?establishment_id=${establishmentId}&date=${date}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchDailyEncashments(
  establishmentId: string,
  date: string
): Promise<{ business_date: string; lines: { mode: string; total: number }[] }> {
  const res = await fetch(`${BASE}/folios/reports/daily-encashments?establishment_id=${establishmentId}&date=${date}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchDebtors(establishmentId: string): Promise<{ folio_id: string; booking_id: string; balance: number }[]> {
  const res = await fetch(`${BASE}/folios/reports/debtors?establishment_id=${establishmentId}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchDepartures(
  establishmentId: string,
  date: string
): Promise<{ business_date: string; departures: { folio_id: string; booking_id: string; balance: number }[] }> {
  const res = await fetch(`${BASE}/folios/reports/departures?establishment_id=${establishmentId}&date=${date}`, { cache: "no-store" });
  return handle(res);
}

export async function fetchDiscrepancy(
  establishmentId: string,
  date: string
): Promise<{ folio_id: string; booking_id: string; type: string; balance: number }[]> {
  const res = await fetch(`${BASE}/folios/reports/discrepancy?establishment_id=${establishmentId}&date=${date}`, { cache: "no-store" });
  return handle(res);
}
