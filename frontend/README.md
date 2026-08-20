# Frontend — Part 9 Core Setup

## Run locally
```bash
cd frontend
npm install
npm run dev
```
Requires the backend running at `http://localhost:8000` (Vite proxies `/api` to it — see `vite.config.ts`).

## What's here
- `src/lib/tokenStore.ts` / `apiClient.ts` — typed axios client, automatic access-token attach, single-flight refresh-on-401
- `src/contexts/AuthContext.tsx` — session bootstrap (silent refresh on page load), login/logout
- `src/contexts/ToastContext.tsx` — global toast notifications
- `src/components/ErrorBoundary.tsx` — catches render errors app-wide
- `src/components/ProtectedRoute.tsx` — redirects to `/login` if unauthenticated, to `/dashboard` if wrong role
- `src/styles/globals.css` + `tailwind.config.js` — the Part 9 design tokens (ink/parchment/brass palette, Fraunces/Inter/IBM Plex Mono type, `.ledger-table` signature style)

## Known limitation (flagged)
Refresh token is stored in `localStorage` for build-phase simplicity — see the security note at the top of `tokenStore.ts`. Production hardening (Part 11) should move this to an HttpOnly cookie set by the backend.

## Not yet built
Login/Dashboard pages here are functional placeholders only, wiring the auth flow end-to-end. Part 10 builds every screen from the proposal's Section 7 list against this foundation.
