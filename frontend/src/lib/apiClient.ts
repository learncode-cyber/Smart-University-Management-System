import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getAccessToken, setAccessToken, getRefreshToken, setRefreshToken, clearTokens } from "./tokenStore";
import type { ApiErrorBody, TokenResponse } from "@/types/api";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// attach the access token to every outgoing request
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Single-flight refresh: if several requests 401 at the same moment
 * (e.g. a dashboard firing 4 parallel queries right as the access token
 * expires), we don't want 4 concurrent calls to /auth/refresh — that
 * would race the refresh-token ROTATION on the backend (Part 2) and
 * only one of them would win, failing the other three. Instead, the
 * first 401 kicks off ONE refresh call; every other 401 that arrives
 * while it's in flight just awaits the same promise.
 */
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }
  const response = await axios.post<{ access_token: string; expires_in: number }>(
    "/api/v1/auth/refresh",
    { refresh_token: refreshToken }
  );
  setAccessToken(response.data.access_token);
  return response.data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const errorCode = error.response?.data?.error?.code;

    const isAuthEndpoint = originalRequest?.url?.includes("/auth/login") || originalRequest?.url?.includes("/auth/refresh");

    if (error.response?.status === 401 && !isAuthEndpoint && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccessToken = await refreshPromise;
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        // refresh itself failed (refresh token expired/revoked) — the
        // session is genuinely over; clear everything and let
        // ProtectedRoute redirect to /login on next render
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export function extractApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    // our own AppError shape: { error: { code, message } }
    if (data && typeof data === "object" && "error" in data) {
      const inner = (data as { error: unknown }).error;
      if (inner && typeof inner === "object" && "message" in inner) {
        return String((inner as { message: unknown }).message);
      }
      // slowapi's rate-limit handler returns { error: "Rate limit exceeded: ..." } —
      // a plain string, not our {code, message} object — surface it directly
      // rather than silently falling through to a generic message.
      if (typeof inner === "string") return inner;
    }
    if (error.response?.status === 429) {
      return "Too many attempts. Please wait a minute and try again.";
    }
    if (!error.response) {
      return "Couldn't reach the server. Check that the backend is running.";
    }
  }
  return "Something went wrong. Please try again.";
}

export async function loginRequest(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  setAccessToken(response.data.access_token);
  setRefreshToken(response.data.refresh_token);
  return response.data;
}

export async function logoutRequest(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    try {
      await apiClient.post("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // even if the server call fails (e.g. already revoked), we still
      // want to clear local state below — logout should never get the
      // user "stuck" logged in on the client
    }
  }
  clearTokens();
}
