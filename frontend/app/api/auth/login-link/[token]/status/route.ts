import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";

const AUTH_GATEWAY_URL = process.env.AUTH_GATEWAY_URL ?? "http://localhost:8001";

export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const res = await fetch(`${AUTH_GATEWAY_URL}/api/v1/auth/login-link/${token}/status`, { cache: "no-store" });
  const body = await res.blob();
  return new NextResponse(body, { status: res.status, headers: { "content-type": "application/json" } });
}
