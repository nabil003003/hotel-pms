import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";

const AUTH_GATEWAY_URL = process.env.AUTH_GATEWAY_URL ?? "http://localhost:8001";

/**
 * Contrairement à /api/proxy/auth-gateway/[...path] (qui exige un
 * access_token — voir lib/proxy.ts), cet appel doit marcher SANS session :
 * c'est justement le desktop pas-encore-connecté qui génère le QR sur
 * /login (biom.txt Flux B).
 */
export async function POST() {
  const res = await fetch(`${AUTH_GATEWAY_URL}/api/v1/auth/login-link/begin`, { method: "POST" });
  const body = await res.blob();
  return new NextResponse(body, { status: res.status, headers: { "content-type": "application/json" } });
}
