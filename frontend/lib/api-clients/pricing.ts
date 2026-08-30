export interface Season {
  id: string;
  establishment_id: string;
  label: string;
  date_debut: string;
  date_fin: string;
  is_active: boolean;
}

export interface RateGridEntry {
  id: string;
  establishment_id: string;
  room_category: string;
  season_id: string;
  regime: string;
  prix_ttc: number;
  prix_ht: number;
  tva_rate: number;
}

export interface TaxConfig {
  id: string;
  establishment_id: string;
  type: string;
  taux_ou_montant: number;
  mode_calcul: string;
  applicable_from: string;
  applicable_to: string | null;
  is_active: boolean;
}

export interface ExtrasCatalogItem {
  id: string;
  establishment_id: string;
  categorie: string;
  libelle: string;
  description: string | null;
  prix_ht: number;
  tva_rate: number;
  prix_ttc: number;
  is_active: boolean;
}

export interface PartnerRate {
  id: string;
  establishment_id: string;
  partner_id: string;
  season_id: string;
  room_category: string;
  regime: string;
  tarif_negocie: number;
  commission_pct: number;
}

export interface Package {
  id: string;
  establishment_id: string;
  label: string;
  description: string | null;
  prix_global_ttc: number;
  ventilation: Record<string, number>;
  is_active: boolean;
  valid_from: string | null;
  valid_to: string | null;
}

export interface RateCalculateResult {
  room_category: string;
  regime: string;
  nights: { date: string; season_id: string; prix_ttc: number }[];
  total_ttc: number;
}

const BASE = "/api/proxy/pricing/pricing";
const RATES_BASE = "/api/proxy/pricing/rates";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  return response.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return handle<T>(res);
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return handle<T>(res);
}

// --------------------------------------------------------------- seasons ---

export async function fetchSeasons(establishmentId: string): Promise<Season[]> {
  const res = await fetch(`${BASE}/${establishmentId}/seasons`, { cache: "no-store" });
  return handle<Season[]>(res);
}

export async function createSeason(
  establishmentId: string,
  input: { label: string; date_debut: string; date_fin: string }
): Promise<Season> {
  return post<Season>(`${BASE}/${establishmentId}/seasons`, input);
}

export async function updateSeason(
  establishmentId: string,
  seasonId: string,
  input: { label?: string; date_debut?: string; date_fin?: string; is_active?: boolean }
): Promise<Season> {
  return patch<Season>(`${BASE}/${establishmentId}/seasons/${seasonId}`, input);
}

// ------------------------------------------------------------- rate grid ---

export async function fetchRateGrid(establishmentId: string): Promise<RateGridEntry[]> {
  const res = await fetch(`${BASE}/${establishmentId}/rate-grid`, { cache: "no-store" });
  return handle<RateGridEntry[]>(res);
}

export async function createRateGridEntry(
  establishmentId: string,
  input: { room_category: string; season_id: string; regime: string; prix_ttc: number; prix_ht: number; tva_rate: number }
): Promise<RateGridEntry> {
  return post<RateGridEntry>(`${BASE}/${establishmentId}/rate-grid`, input);
}

export async function updateRateGridEntry(
  establishmentId: string,
  rateGridId: string,
  input: { prix_ttc?: number; prix_ht?: number; tva_rate?: number }
): Promise<RateGridEntry> {
  return patch<RateGridEntry>(`${BASE}/${establishmentId}/rate-grid/${rateGridId}`, input);
}

// ------------------------------------------------------------------ taxes --

export async function fetchTaxes(establishmentId: string): Promise<TaxConfig[]> {
  const res = await fetch(`${BASE}/${establishmentId}/taxes`, { cache: "no-store" });
  return handle<TaxConfig[]>(res);
}

export async function createTax(
  establishmentId: string,
  input: { type: string; taux_ou_montant: number; mode_calcul: string }
): Promise<TaxConfig> {
  return post<TaxConfig>(`${BASE}/${establishmentId}/taxes`, input);
}

export async function updateTax(
  establishmentId: string,
  taxId: string,
  input: { taux_ou_montant?: number; is_active?: boolean }
): Promise<TaxConfig> {
  return patch<TaxConfig>(`${BASE}/${establishmentId}/taxes/${taxId}`, input);
}

// ----------------------------------------------------------------- extras --

export async function fetchExtras(establishmentId: string): Promise<ExtrasCatalogItem[]> {
  const res = await fetch(`${BASE}/${establishmentId}/extras`, { cache: "no-store" });
  return handle<ExtrasCatalogItem[]>(res);
}

export async function createExtra(
  establishmentId: string,
  input: { categorie: string; libelle: string; description?: string; prix_ht: number; tva_rate: number }
): Promise<ExtrasCatalogItem> {
  return post<ExtrasCatalogItem>(`${BASE}/${establishmentId}/extras`, input);
}

export async function updateExtra(
  establishmentId: string,
  itemId: string,
  input: { libelle?: string; description?: string; is_active?: boolean }
): Promise<ExtrasCatalogItem> {
  return patch<ExtrasCatalogItem>(`${BASE}/${establishmentId}/extras/${itemId}`, input);
}

// ---------------------------------------------------------- partner rates --

export async function fetchPartnerRates(establishmentId: string): Promise<PartnerRate[]> {
  const res = await fetch(`${BASE}/${establishmentId}/partner-rates`, { cache: "no-store" });
  return handle<PartnerRate[]>(res);
}

export async function createPartnerRate(
  establishmentId: string,
  input: {
    partner_id: string;
    season_id: string;
    room_category: string;
    regime: string;
    tarif_negocie: number;
    commission_pct: number;
  }
): Promise<PartnerRate> {
  return post<PartnerRate>(`${BASE}/${establishmentId}/partner-rates`, input);
}

export async function updatePartnerRate(
  establishmentId: string,
  rateId: string,
  input: { tarif_negocie?: number; commission_pct?: number }
): Promise<PartnerRate> {
  return patch<PartnerRate>(`${BASE}/${establishmentId}/partner-rates/${rateId}`, input);
}

// -------------------------------------------------------------- packages --

export async function fetchPackages(establishmentId: string): Promise<Package[]> {
  const res = await fetch(`${BASE}/${establishmentId}/packages`, { cache: "no-store" });
  return handle<Package[]>(res);
}

export async function createPackage(
  establishmentId: string,
  input: {
    label: string;
    description?: string;
    prix_global_ttc: number;
    ventilation: Record<string, number>;
    valid_from?: string;
    valid_to?: string;
  }
): Promise<Package> {
  return post<Package>(`${BASE}/${establishmentId}/packages`, input);
}

export async function updatePackage(
  establishmentId: string,
  packageId: string,
  input: { is_active?: boolean; prix_global_ttc?: number }
): Promise<Package> {
  return patch<Package>(`${BASE}/${establishmentId}/packages/${packageId}`, input);
}

// ------------------------------------------------------------ rate lookup --

export async function calculateRate(input: {
  establishment_id: string;
  room_category: string;
  regime: string;
  date_from: string;
  date_to: string;
}): Promise<RateCalculateResult> {
  const params = new URLSearchParams(input);
  const res = await fetch(`${RATES_BASE}/calculate?${params}`, { cache: "no-store" });
  return handle<RateCalculateResult>(res);
}
