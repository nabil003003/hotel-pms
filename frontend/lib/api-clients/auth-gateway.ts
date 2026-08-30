export interface AppUser {
  id: string;
  email: string;
  display_name: string | null;
  is_super_admin: boolean;
  is_active: boolean;
}

export interface EstablishmentUser {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  role: string;
  created_at: string;
  temp_password: string | null;
}

export interface UserCreateResult {
  user: AppUser;
  temp_password: string;
}

const BASE = "/api/proxy/auth-gateway/auth";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function fetchEstablishmentUsers(establishmentId: string): Promise<EstablishmentUser[]> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/users`, { cache: "no-store" });
  return handle<EstablishmentUser[]>(res);
}

export async function updateEstablishmentUserRole(
  establishmentId: string,
  userId: string,
  role: string
): Promise<EstablishmentUser> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/users/${userId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ role }),
  });
  return handle<EstablishmentUser>(res);
}

export async function deactivateEstablishmentUser(
  establishmentId: string,
  userId: string
): Promise<EstablishmentUser> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/users/${userId}`, {
    method: "DELETE",
  });
  return handle<EstablishmentUser>(res);
}

export async function deleteEstablishmentUserPermanently(establishmentId: string, userId: string): Promise<void> {
  const res = await fetch(`${BASE}/establishments/${establishmentId}/users/${userId}/permanent`, {
    method: "DELETE",
  });
  return handle<void>(res);
}

export async function elevate(establishmentId: string): Promise<{ token: string; expires_at: string }> {
  const res = await fetch(`${BASE}/elevate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ establishment_id: establishmentId }),
  });
  return handle(res);
}

export async function createUser(input: {
  username: string;
  email: string;
  role: string;
  establishment_ids: string[];
  is_super_admin: boolean;
}): Promise<UserCreateResult> {
  const res = await fetch(`${BASE}/users`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<UserCreateResult>(res);
}
