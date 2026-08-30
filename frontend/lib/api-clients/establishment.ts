export interface Establishment {
  id: string;
  name: string;
  address: string | null;
  city: string;
  country: string;
  phone: string | null;
  email: string | null;
  total_rooms: number;
  is_active: boolean;
}

export interface RoomCreateInput {
  numero: string;
  categorie: string;
  floor: number;
  capacity_adults: number;
  capacity_children: number;
}

export interface Room {
  id: string;
  establishment_id: string;
  numero: string;
  categorie: string;
  floor: number;
  capacity_adults: number;
  capacity_children: number;
  is_active: boolean;
}

export interface EstablishmentServiceItem {
  id: string;
  establishment_id: string;
  code: string;
  label: string;
  description: string | null;
  prix_ht: number;
  tva_rate: number;
  prix_ttc: number;
  category: string;
  is_active: boolean;
}

export interface OtaMapping {
  id: string;
  establishment_id: string;
  ota_name: string;
  ota_property_id: string;
  ota_room_type_id: string | null;
  internal_room_category: string | null;
  is_active: boolean;
}

const BASE = "/api/proxy/establishment";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail?.message ?? body.detail ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchEstablishments(): Promise<Establishment[]> {
  const res = await fetch(`${BASE}/establishments`, { cache: "no-store" });
  return handle<Establishment[]>(res);
}

export async function createEstablishment(input: {
  name: string;
  address?: string;
  city?: string;
  country?: string;
  phone?: string;
  email?: string;
  total_rooms: number;
}): Promise<Establishment> {
  const res = await fetch(`${BASE}/establishments`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Establishment>(res);
}

export async function createRoomsBulk(
  establishmentId: string,
  rooms: RoomCreateInput[]
): Promise<unknown> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/rooms`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(rooms),
  });
  return handle(res);
}

export async function updateEstablishment(
  id: string,
  input: { name?: string; address?: string; phone?: string; email?: string; is_active?: boolean }
): Promise<Establishment> {
  const res = await fetch(`${BASE}/establishments/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Establishment>(res);
}

export async function fetchRooms(establishmentId: string): Promise<Room[]> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/rooms`, { cache: "no-store" });
  return handle<Room[]>(res);
}

export async function updateRoom(
  establishmentId: string,
  roomId: string,
  input: Partial<RoomCreateInput>
): Promise<Room> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/rooms/${roomId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Room>(res);
}

export async function deleteRoom(establishmentId: string, roomId: string): Promise<Room> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/rooms/${roomId}`, {
    method: "DELETE",
  });
  return handle<Room>(res);
}

export async function fetchEstablishmentServices(establishmentId: string): Promise<EstablishmentServiceItem[]> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/services`, { cache: "no-store" });
  return handle<EstablishmentServiceItem[]>(res);
}

export async function createEstablishmentService(
  establishmentId: string,
  input: { code: string; label: string; description?: string; prix_ht: number; tva_rate: number; category: string }
): Promise<EstablishmentServiceItem> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/services`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<EstablishmentServiceItem>(res);
}

export async function fetchOtaMappings(establishmentId: string): Promise<OtaMapping[]> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/ota-mappings`, { cache: "no-store" });
  return handle<OtaMapping[]>(res);
}

export async function upsertOtaMapping(
  establishmentId: string,
  input: {
    ota_name: string;
    ota_property_id: string;
    ota_room_type_id?: string;
    internal_room_category?: string;
  }
): Promise<OtaMapping> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/ota-mappings`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<OtaMapping>(res);
}
