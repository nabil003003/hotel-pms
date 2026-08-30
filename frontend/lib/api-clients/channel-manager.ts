export interface ChannelConnection {
  id: string;
  establishment_id: string;
  ota_name: string;
  is_active: boolean;
  two_way_sync_enabled: boolean;
  last_sync_at: string | null;
}

const BASE = "/api/proxy/channel-manager/channel";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchConnections(establishmentId: string): Promise<ChannelConnection[]> {
  const res = await fetch(`${BASE}/connections/${establishmentId}`, { cache: "no-store" });
  return handle<ChannelConnection[]>(res);
}

export async function upsertConnection(
  establishmentId: string,
  input: { ota_name: string; is_active: boolean; two_way_sync_enabled: boolean }
): Promise<ChannelConnection> {
  const res = await fetch(`${BASE}/connections/${establishmentId}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<ChannelConnection>(res);
}

export async function fetchPerformance(
  establishmentId: string,
  period: string
): Promise<{ period: string; by_ota: Record<string, Record<string, number>> }> {
  const res = await fetch(`${BASE}/performance?establishment_id=${establishmentId}&period=${period}`, {
    cache: "no-store",
  });
  return handle(res);
}
