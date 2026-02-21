import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = () =>
  process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * Catch-all API proxy. Forwards /api/* requests to the backend.
 * Route handlers like /api/health take priority over this catch-all.
 *
 * Why a route handler instead of next.config.ts rewrites:
 * - Rewrites buffer SSE responses (breaks streaming)
 * - Rewrites bake BACKEND_URL at build time (can't change at runtime in Docker)
 */
async function proxyRequest(request: NextRequest) {
  // Use raw URL to preserve trailing slashes. nextUrl.pathname normalizes them away,
  // which causes FastAPI 307 redirects that lose auth headers and POST bodies.
  const rawPathname = new URL(request.url).pathname;
  const backendPath = rawPathname.replace(/^\/api/, "");
  const backendUrl = `${BACKEND_URL()}${backendPath}${request.nextUrl.search}`;

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

  const isSSE = backendContentType?.includes("text/event-stream") ?? false;

  if (isSSE) {
    responseHeaders.set("Cache-Control", "no-cache, no-transform");
    responseHeaders.set("Connection", "keep-alive");
    responseHeaders.set("X-Accel-Buffering", "no");
  }

  // Forward content-disposition for file downloads
  const contentDisposition = backendResponse.headers.get("content-disposition");
  if (contentDisposition)
    responseHeaders.set("Content-Disposition", contentDisposition);

  if (isSSE && backendResponse.body) {
    // Explicitly pipe chunks for SSE to prevent buffering
    const reader = backendResponse.body.getReader();
    const stream = new ReadableStream({
      async pull(controller) {
        const { done, value } = await reader.read();
        if (done) {
          controller.close();
          return;
        }
        controller.enqueue(value);
      },
      cancel() {
        reader.cancel();
      },
    });

    return new Response(stream, {
      status: backendResponse.status,
      headers: responseHeaders,
    });
  }

  // 204 No Content must not have a body — Response constructor rejects it
  if (backendResponse.status === 204) {
    return new Response(null, { status: 204, headers: responseHeaders });
  }

  // For non-streaming: read full body and return it to avoid Content-Length mismatches
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
