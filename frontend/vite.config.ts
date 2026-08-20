import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api to the FastAPI backend so the frontend never
// needs CORS configured for local development. Target is configurable via
// VITE_BACKEND_URL so the same config works for `npm run dev` locally
// (defaults to localhost:8000) and inside Docker Compose (set to
// http://backend:8000, the service name — see docker-compose.yml).
//
// IMPORTANT: tsconfig.json's `paths: { "@/*": ["src/*"] }` only tells
// TypeScript's type-checker about the alias — it has ZERO effect on Vite's
// actual dev-server/bundler module resolution. Vite needs its OWN alias
// config below, or every `@/...` import fails at runtime with "Failed to
// resolve import" even though `tsc` reports no errors. Both must be kept
// in sync any time the alias target changes.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
