import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { COOKIE_SESSION } from "@/lib/auth/constants";
export const dynamic = "force-dynamic";

export async function GET() {
  const cookieStore = await cookies();
  const raw = cookieStore.get(COOKIE_SESSION)?.value;

  if (!raw) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  try {
    const claims = JSON.parse(raw);
    return NextResponse.json({ authenticated: true, claims });
  } catch {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }
}
