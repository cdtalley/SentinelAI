export function getApiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  return (base || "http://localhost:8000").replace(/\/$/, "");
}

export function getApiKey(): string | undefined {
  const k = process.env.NEXT_PUBLIC_API_KEY;
  return k?.trim() || undefined;
}

export function getWsAlertsUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, "");
  if (explicit) {
    return appendApiKeyQuery(explicit);
  }
  const base = getApiBase();
  const u = new URL(base);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  u.pathname = "/api/v1/ws/alerts";
  u.search = "";
  u.hash = "";
  return appendApiKeyQuery(u.toString());
}

function appendApiKeyQuery(url: string): string {
  const key = getApiKey();
  if (!key) return url;
  const u = new URL(url);
  u.searchParams.set("api_key", key);
  return u.toString();
}
