import { TokenResponse, RefreshRequest } from "@/types/auth";

const TOKEN_PREFIX = "spectra";
const ACCESS_TOKEN_KEY = `${TOKEN_PREFIX}_access_token`;
const REFRESH_TOKEN_KEY = `${TOKEN_PREFIX}_refresh_token`;

const BASE_URL = "/api";

/**
 * Store authentication tokens in localStorage
 */
export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Retrieve access token from localStorage
 */
export function getAccessToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }
  return null;
}

/**
 * Retrieve refresh token from localStorage
 */
function getRefreshToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }
  return null;
}

/**
 * Clear all authentication tokens from localStorage
 */
export function clearTokens(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

/**
 * Check if user is authenticated (has access token)
 */
export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

/**
 * Attempt to refresh the access token using the refresh token
 */
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }

  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken } as RefreshRequest),
    });

    if (!response.ok) {
      clearTokens();
      return false;
    }

    const data: TokenResponse = await response.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch (error) {
    clearTokens();
    return false;
  }
}

interface RequestOptions {
  method: string;
  headers: Record<string, string>;
  body?: string;
}

/**
 * Internal fetch wrapper with automatic token injection and refresh
 */
async function fetchWithAuth(
  path: string,
  options: RequestOptions
): Promise<Response> {
  const accessToken = getAccessToken();

  // Add Authorization header if token exists
  if (accessToken) {
    options.headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let response = await fetch(`${BASE_URL}${path}`, options);

  // If 401 Unauthorized, attempt token refresh
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();

    if (refreshed) {
      // Retry original request with new token
      const newAccessToken = getAccessToken();
      if (newAccessToken) {
        options.headers["Authorization"] = `Bearer ${newAccessToken}`;
      }
      response = await fetch(`${BASE_URL}${path}`, options);
    } else {
      // Refresh failed, redirect to login
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  }

  return response;
}

/**
 * API client for making requests to the backend.
 * Automatically injects Authorization header and handles token refresh.
 */
export const apiClient = {
  /**
   * GET request
   */
  async get(path: string): Promise<Response> {
    return fetchWithAuth(path, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * POST request with JSON body
   */
  async post(path: string, body: any): Promise<Response> {
    return fetchWithAuth(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  },

  /**
   * PATCH request with JSON body
   */
  async patch(path: string, body: any): Promise<Response> {
    return fetchWithAuth(path, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  },

  /**
   * DELETE request
   */
  async delete(path: string): Promise<Response> {
    return fetchWithAuth(path, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * POST request with FormData (for file uploads)
   */
  async upload(path: string, formData: FormData): Promise<Response> {
    const accessToken = getAccessToken();

    const headers: Record<string, string> = {};
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }

    let response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers,
      body: formData,
    });

    // Handle 401 with token refresh
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();

      if (refreshed) {
        const newAccessToken = getAccessToken();
        if (newAccessToken) {
          headers["Authorization"] = `Bearer ${newAccessToken}`;
        }
        response = await fetch(`${BASE_URL}${path}`, {
          method: "POST",
          headers,
          body: formData,
        });
      } else {
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    return response;
  },
};
