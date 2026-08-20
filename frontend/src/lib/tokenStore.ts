/**
 * Token storage.
 *
 * SECURITY NOTE (flagged, same tradeoff noted on the backend in Part 2):
 * the refresh token is kept in localStorage here for build-phase
 * simplicity, which is vulnerable to XSS reading it. The production-
 * hardened approach is an HttpOnly, Secure, SameSite=strict cookie set
 * directly by the backend, so frontend JS never touches it at all —
 * flagged as a Part 11 deployment-hardening item, not implemented here
 * to avoid blocking the rest of the build on a cookie/CORS rework.
 *
 * The access token is kept ONLY in memory (a module-level variable) —
 * never localStorage — so a page refresh always re-derives it via
 * /auth/refresh rather than trusting a possibly-stale copy on disk.
 */
const REFRESH_TOKEN_KEY = "ums_refresh_token";

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export function clearTokens(): void {
  accessToken = null;
  setRefreshToken(null);
}
