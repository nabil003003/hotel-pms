export interface MarketSegment {
  id: string;
  establishment_id: string;
  code: string;
  label: string;
  category: "DIRECT" | "OTA" | "PARTENAIRES";
  color: string;
  is_active: boolean;
}

export interface Booking {
  id: string;
  establishment_id: string;
  customer_id: string;
  room_id: string;
  market_segment_id: string;
  status: string;
  option_expiry_date: string | null;
  check_in_date: string;
  check_out_date: string;
  regime: string;
  partner_id: string | null;
  taxes_payment_mode: string;
  total_amount: number | null;
  deposit_amount: number;
  adults: number;
  children: number;
  notes: string | null;
  source: string;
  ota_reference: string | null;
  created_at: string;
}

export interface BookingCreateInput {
  establishment_id: string;
  market_segment_id?: string;
  market_segment_category?: string;
  room_category: string;
  check_in_date: string;
  check_out_date: string;
  regime: string;
  taxes_payment_mode: string;
  adults: number;
  children: number;
  customer: { first_name: string; last_name: string; email?: string; phone?: string };
  source: string;
  deposit_paid: boolean;
  partner_id?: string;
}

export interface Customer {
  id: string;
  establishment_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  is_vip: boolean;
  preferences: Record<string, unknown>;
  consent_marketing: boolean;
}

export interface RoomShiftResult {
  booking_id: string;
  old_room_id: string;
  new_room_id: string;
  new_amount: number | null;
  delta: number;
}

const BASE = "/api/proxy/reservation";

export type ReservationError = Error & {
  code?: string;
  conflicting_booking_id?: string;
  retry_after?: number;
};

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? JSON.stringify(detail);
    const err = new Error(message ?? `Request failed (${response.status})`) as ReservationError;
    if (detail?.code) err.code = detail.code;
    if (detail?.conflicting_booking_id) err.conflicting_booking_id = detail.conflicting_booking_id;
    if (detail?.retry_after !== undefined) err.retry_after = detail.retry_after;
    throw err;
  }
  return response.json();
}

export async function fetchMarketSegments(establishmentId: string): Promise<MarketSegment[]> {
  const res = await fetch(`${BASE}/market-segments/${establishmentId}`, { cache: "no-store" });
  return handle<MarketSegment[]>(res);
}

export async function createMarketSegment(
  establishmentId: string,
  input: { code: string; label: string; category: string; color: string }
): Promise<MarketSegment> {
  const res = await fetch(`${BASE}/market-segments/${establishmentId}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<MarketSegment>(res);
}

export async function updateMarketSegment(
  establishmentId: string,
  segmentId: string,
  input: { label?: string; color?: string; is_active?: boolean }
): Promise<MarketSegment> {
  const res = await fetch(`${BASE}/market-segments/${establishmentId}/${segmentId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<MarketSegment>(res);
}

// ------------------------------------------------------------- customers ---

export async function fetchCustomers(establishmentId: string): Promise<Customer[]> {
  const res = await fetch(`${BASE}/customers/${establishmentId}`, { cache: "no-store" });
  return handle<Customer[]>(res);
}

export async function createCustomer(
  establishmentId: string,
  input: { first_name: string; last_name: string; email?: string; phone?: string; is_vip?: boolean }
): Promise<Customer> {
  const res = await fetch(`${BASE}/customers/${establishmentId}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Customer>(res);
}

export async function updateCustomer(
  establishmentId: string,
  customerId: string,
  input: { first_name?: string; last_name?: string; email?: string; phone?: string; is_vip?: boolean }
): Promise<Customer> {
  const res = await fetch(`${BASE}/customers/${establishmentId}/${customerId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Customer>(res);
}

// ---------------------------------------------------------- availability ---

export async function checkAvailability(input: {
  establishment_id: string;
  room_id: string;
  check_in_date: string;
  check_out_date: string;
}): Promise<{ available: boolean; conflicting_booking_id: string | null }> {
  const res = await fetch(`${BASE}/bookings/check-availability`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle(res);
}

export async function fetchBookings(
  establishmentId: string,
  fromDate: string,
  toDate: string,
  status?: string
): Promise<Booking[]> {
  const params = new URLSearchParams({
    establishment_id: establishmentId,
    from_date: fromDate,
    to_date: toDate,
  });
  if (status) params.set("status", status);
  const res = await fetch(`${BASE}/bookings?${params}`, { cache: "no-store" });
  return handle<Booking[]>(res);
}

/**
 * Filtre exact sur `check_in_date` (Sprint 7, bug réel trouvé par les tests
 * E2E) — `fetchBookings(est, today, today, status)` semblait équivalent
 * mais ne l'est pas : `from_date`/`to_date` sont un filtre de plage ouverte
 * (`check_out_date > from_date` ET `check_in_date < to_date`), qui exclut
 * silencieusement toute arrivée exactement le jour `to_date` quand
 * `from_date === to_date`. Utiliser ce filtre dédié pour "arrivées du jour
 * J" plutôt que de détourner le filtre de plage.
 */
export async function fetchBookingsByCheckInDate(
  establishmentId: string,
  checkInDate: string,
  status?: string
): Promise<Booking[]> {
  const params = new URLSearchParams({ establishment_id: establishmentId, check_in_date: checkInDate });
  if (status) params.set("status", status);
  const res = await fetch(`${BASE}/bookings?${params}`, { cache: "no-store" });
  return handle<Booking[]>(res);
}

export async function createBooking(input: BookingCreateInput): Promise<Booking> {
  const res = await fetch(`${BASE}/bookings`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<Booking>(res);
}

export async function updateBookingStatus(bookingId: string, newStatus: string, reason?: string): Promise<Booking> {
  const res = await fetch(`${BASE}/bookings/${bookingId}/status`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ new_status: newStatus, reason: reason ?? null }),
  });
  return handle<Booking>(res);
}

export async function cancelBooking(bookingId: string, reason?: string): Promise<Booking> {
  return updateBookingStatus(bookingId, "status_cancelled", reason);
}

export async function shiftRoom(
  bookingId: string,
  input: {
    new_room_id: string;
    new_room_category?: string;
    new_check_in_date?: string;
    new_check_out_date?: string;
    same_category: boolean;
    keep_current_rate?: boolean;
    force?: boolean;
    reason?: string;
    elevation_token?: string;
  }
): Promise<RoomShiftResult> {
  const res = await fetch(`${BASE}/bookings/${bookingId}/room`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle<RoomShiftResult>(res);
}
