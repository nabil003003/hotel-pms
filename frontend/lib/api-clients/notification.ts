export interface Notification {
  id: string;
  establishment_id: string;
  event_type: string;
  channel: string;
  recipient_role: string;
  subject: string;
  body: string;
  status: string;
  related_entity_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
  sent_at: string | null;
  read_at: string | null;
}

export const STAFF_ROLES = [
  "receptionniste",
  "gouvernante",
  "femme_de_chambre",
  "manager",
  "admin",
  "comptable",
  "agence_externe",
] as const;

export const STAFF_ROLE_LABELS: Record<string, string> = {
  receptionniste: "Réceptionniste",
  gouvernante: "Gouvernante",
  femme_de_chambre: "Femme de chambre",
  manager: "Manager",
  admin: "Admin",
  comptable: "Comptable",
  agence_externe: "Agence externe",
};

const BASE = "/api/proxy/notification/notifications";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    throw new Error(message ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchNotifications(establishmentId: string, eventType?: string): Promise<Notification[]> {
  const params = new URLSearchParams({ establishment_id: establishmentId });
  if (eventType) params.set("event_type", eventType);
  const res = await fetch(`${BASE}?${params}`, { cache: "no-store" });
  return handle<Notification[]>(res);
}

export async function fetchNotification(notificationId: string): Promise<Notification> {
  const res = await fetch(`${BASE}/${notificationId}`, { cache: "no-store" });
  return handle<Notification>(res);
}

export async function fetchMyNotifications(establishmentId: string, unreadOnly = false): Promise<Notification[]> {
  const params = new URLSearchParams({ establishment_id: establishmentId });
  if (unreadOnly) params.set("unread_only", "true");
  const res = await fetch(`${BASE}/mine?${params}`, { cache: "no-store" });
  return handle<Notification[]>(res);
}

export async function markNotificationRead(notificationId: string): Promise<Notification> {
  const res = await fetch(`${BASE}/${notificationId}/read`, { method: "PATCH" });
  return handle<Notification>(res);
}

export async function sendMessage(
  establishmentId: string,
  recipientRole: string,
  subject: string,
  body: string
): Promise<Notification> {
  const res = await fetch(`${BASE}/message`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ establishment_id: establishmentId, recipient_role: recipientRole, subject, body }),
  });
  return handle<Notification>(res);
}
