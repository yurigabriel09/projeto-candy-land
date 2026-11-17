const configuredApiBase = String(import.meta.env.VITE_API_URL || "").trim().replace(/\/+$/, "");

// No Vite dev server, use same-origin paths so localhost and ngrok both pass
// through vite.config.js -> Flask. This avoids browser CORS preflight failures.
// Production can set VITE_API_URL to the public API origin or use an Nginx proxy.
export const API_BASE_URL = import.meta.env.DEV ? "" : configuredApiBase;

export function apiUrl(path) {
  const normalizedPath = String(path || "").replace(/^\/+/, "");
  return `${API_BASE_URL}/${normalizedPath}`;
}
