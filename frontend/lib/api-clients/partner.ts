export interface Partner {
  id: string;
  establishment_id: string;
  type: string;
  nom: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  ice: string | null;
  rc: string | null;
  address: string | null;
  payment_terms: number;
  is_active: boolean;
}

const BASE = "/api/proxy/partner/partners";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchPartners(establishmentId: string): Promise<Partner[]> {
  const res = await fetch(`${BASE}/${establishmentId}`, { cache: "no-store" });
  return handle<Partner[]>(res);
}

export async function createPartner(
  establishmentId: string,
  input: { type: string; nom: string; contact_name?: string; email?: string; phone?: string; payment_terms: number }
): Promise<Partner> {
  const res = await fetch(`${BASE}/${establishmentId}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Partner>(res);
}

export async function updatePartner(
  establishmentId: string,
  partnerId: string,
  input: { nom?: string; contact_name?: string; email?: string; phone?: string; payment_terms?: number; is_active?: boolean }
): Promise<Partner> {
  const res = await fetch(`${BASE}/${establishmentId}/${partnerId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Partner>(res);
}

export async function deletePartner(establishmentId: string, partnerId: string): Promise<Partner> {
  const res = await fetch(`${BASE}/${establishmentId}/${partnerId}`, { method: "DELETE" });
  return handle<Partner>(res);
}
