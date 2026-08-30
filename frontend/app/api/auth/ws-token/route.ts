import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { COOKIE_ACCESS_TOKEN } from "@/lib/auth/constants";
export const dynamic = "force-dynamic";

/**
 * Expose le JWT brut au JS client, UNIQUEMENT pour ouvrir la connexion
 * WebSocket (housekeeping-service n'accepte pas de header Authorization sur
 * le handshake WS, voir services/housekeeping-service/app/api/v1/endpoints.py).
 * Compromis assumé : le token quitte le cookie httpOnly pour cet usage
 * précis, via un endpoint same-origin qui exige déjà la session active.
 */
export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_ACCESS_TOKEN)?.value;

  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  return NextResponse.json({ token });
}
