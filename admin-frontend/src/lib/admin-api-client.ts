const ADMIN_TOKEN_KEY = "spectra_admin_token";

/**
 * Store admin token in localStorage
 */
export function setAdminToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
  }
}

/**
 * Retrieve admin token from localStorage
 */
export function getAdminToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(ADMIN_TOKEN_KEY);
  }
  return null;
}

/**
 * Clear admin token from localStorage
 */
export function clearAdminToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
  }
}

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

/**
 * Fetch wrapper with automatic admin token injection and X-Admin-Token interception.
 * Uses relative paths so Next.js rewrites proxy to the backend.
 */
async function fetchWithAdminAuth(
  path: string,
  options: RequestOptions = {}
): Promise<Response> {
  const token = getAdminToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  // Intercept X-Admin-Token header for sliding window session renewal
  const newToken = response.headers.get("X-Admin-Token");
  if (newToken) {
    setAdminToken(newToken);
  }

  // Redirect to login on 401 Unauthorized
  if (response.status === 401) {
    clearAdminToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return response;
}

/**
 * Admin API client for making authenticated requests to the backend.
 * Automatically injects Authorization header, intercepts X-Admin-Token
 * for sliding window session renewal, and redirects to /login on 401.
 */
export const adminApiClient = {
  async get(path: string): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "GET",
    });
  },

  async post(path: string, body?: unknown): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async patch(path: string, body?: unknown): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async put(path: string, body?: unknown): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async delete(path: string, body?: unknown): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "DELETE",
      body: body ? JSON.stringify(body) : undefined,
    });
  },
};
