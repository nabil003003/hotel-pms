export interface Room {
  id: string;
  establishment_id: string;
  numero: string;
  categorie: string;
  floor: number;
  statut: "Sale" | "Nettoyage" | "Propre" | "Contrôlée" | "Bloquée";
  motif_blocage: string | null;
  blocked_reason: string | null;
  blocked_at: string | null;
  is_active: boolean;
}

export interface RoomIncident {
  id: string;
  room_id: string;
  incident_type: string;
  description: string | null;
  photo_url: string | null;
  reported_by: string;
  reported_at: string;
  resolved_at: string | null;
}

export interface StatusHistoryEntry {
  id: string;
  old_status: string | null;
  new_status: string;
  changed_by: string;
  changed_at: string;
  reason: string | null;
}

const BASE = "/api/proxy/housekeeping";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail?.message ?? body.detail ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchRooms(establishmentId: string): Promise<Room[]> {
  const res = await fetch(`${BASE}/rooms?establishment_id=${establishmentId}`, {
    cache: "no-store",
  });
  return handle<Room[]>(res);
}

export async function changeRoomStatus(
  roomId: string,
  newStatus: string,
  reason?: string
): Promise<Room> {
  const res = await fetch(`${BASE}/rooms/${roomId}/status`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ new_status: newStatus, reason: reason ?? null }),
  });
  return handle<Room>(res);
}

export async function reportIncident(
  roomId: string,
  incidentType: string,
  description?: string
): Promise<RoomIncident> {
  const res = await fetch(`${BASE}/rooms/${roomId}/incidents`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ incident_type: incidentType, description: description ?? null }),
  });
  return handle<RoomIncident>(res);
}

export async function fetchRoomHistory(roomId: string): Promise<StatusHistoryEntry[]> {
  const res = await fetch(`${BASE}/rooms/${roomId}/history`, { cache: "no-store" });
  return handle<StatusHistoryEntry[]>(res);
}

export async function fetchRoomIncidents(roomId: string): Promise<RoomIncident[]> {
  const res = await fetch(`${BASE}/rooms/${roomId}/incidents`, { cache: "no-store" });
  return handle<RoomIncident[]>(res);
}
