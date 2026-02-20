import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = () =>
  process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * Catch-all API proxy for admin frontend.
 * Forwards /api/* to BACKEND_URL/api/* (preserves /api/ prefix for admin routes).
 * Route handlers like /api/health take priority over this catch-all.
 *
 * Why a route handler instead of next.config.ts rewrites:
 * - Rewrites buffer SSE responses (breaks streaming)
 * - Rewrites bake BACKEND_URL at build time (can't change at runtime in Docker)
 */
async function proxyRequest(request: NextRequest) {
  // Admin frontend keeps /api/ prefix: /api/admin/users → BACKEND_URL/api/admin/users
  // Use raw URL to preserve trailing slashes.
  const rawPathname = new URL(request.url).pathname;
  const backendUrl = `${BACKEND_URL()}${rawPathname}${request.nextUrl.search}`;

  const headers: Record<string, string> = {};
  const authorization = request.headers.get("authorization");
  if (authorization) headers["Authorization"] = authorization;

  const contentType = request.headers.get("content-type");
  if (contentType) headers["Content-Type"] = contentType;

  const body =
    request.method !== "GET" && request.method !== "HEAD"
      ? await request.arrayBuffer()
      : undefined;

  let backendResponse: Response;
  try {
    backendResponse = await fetch(backendUrl, {
      method: request.method,
      headers,
      body,
      redirect: "follow",
    });
  } catch (err) {
    console.error("[proxy] fetch failed:", backendUrl, err);
    return new Response(JSON.stringify({ detail: "Backend unavailable" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  const responseHeaders = new Headers();
  const backendContentType = backendResponse.headers.get("content-type");
  if (backendContentType) responseHeaders.set("Content-Type", backendContentType);

  // Forward X-Admin-Token for sliding window session renewal
  const adminToken = backendResponse.headers.get("x-admin-token");
  if (adminToken) responseHeaders.set("X-Admin-Token", adminToken);

  // Forward content-disposition for file downloads
  const contentDisposition = backendResponse.headers.get("content-disposition");
  if (contentDisposition)
    responseHeaders.set("Content-Disposition", contentDisposition);

  // Read full body to avoid Content-Length mismatches from redirects
  const responseBody = await backendResponse.arrayBuffer();
  return new Response(responseBody, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export async function GET(request: NextRequest) {
  return proxyRequest(request);
}

export async function POST(request: NextRequest) {
  return proxyRequest(request);
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request);
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request);
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request);
}
