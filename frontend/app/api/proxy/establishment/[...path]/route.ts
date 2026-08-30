import { NextRequest } from "next/server";

import { proxyToService } from "@/lib/proxy";
export const dynamic = "force-dynamic";

const TARGET = process.env.ESTABLISHMENT_SERVICE_URL ?? "http://localhost:8002";

type RouteParams = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, { params }: RouteParams) {
  const { path } = await params;
  return proxyToService(request, TARGET, path);
}

export async function PATCH(request: NextRequest, { params }: RouteParams) {
  const { path } = await params;
  return proxyToService(request, TARGET, path);
}

export async function POST(request: NextRequest, { params }: RouteParams) {
  const { path } = await params;
  return proxyToService(request, TARGET, path);
}

export async function DELETE(request: NextRequest, { params }: RouteParams) {
  const { path } = await params;
  return proxyToService(request, TARGET, path);
}
