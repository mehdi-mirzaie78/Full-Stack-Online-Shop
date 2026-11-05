export const roles = ["SUPERADMIN", "PRODUCT_MANAGER", "OPERATOR", "AUDITOR", "CUSTOMER"] as const;
export type Role = typeof roles[number];
export type User = { id: string; phone: string; role: Role; is_active: boolean; is_deleted: boolean; created_at: string };
export const apiBase = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000/api/v1";

export function parseUser(value: unknown): User {
  const user = value as Partial<User> | null;
  if (!user || typeof user.id !== "string" || typeof user.phone !== "string" || !roles.includes(user.role as Role)
    || typeof user.is_active !== "boolean" || typeof user.is_deleted !== "boolean" || typeof user.created_at !== "string") {
    throw new Error("Invalid user response.");
  }
  return user as User;
}

let refreshing: Promise<Response> | undefined;
async function send(path: string, method: string, data?: unknown): Promise<Response> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (method !== "GET") {
    const response = await fetch(`${apiBase}/auth/csrf`, { credentials: "include", cache: "no-store" });
    if (!response.ok) throw new Error("Cannot establish a secure request.");
    const body: unknown = await response.json();
    if (!body || typeof (body as { csrfToken?: unknown }).csrfToken !== "string") throw new Error("Invalid CSRF response.");
    headers["X-CSRFToken"] = (body as { csrfToken: string }).csrfToken;
  }
  return fetch(`${apiBase}/${path}`, { method, headers, credentials: "include", cache: "no-store", ...(data === undefined ? {} : { body: JSON.stringify(data) }) });
}

export async function api(path: string, method = "GET", data?: unknown): Promise<unknown> {
  let response = await send(path, method, data);
  if (response.status === 401 && path !== "auth/refresh") {
    const rotate = async () => {
      if (globalThis.navigator?.locks) {
        return navigator.locks.request("shop-session-refresh", async () => {
          const current = await send("auth/me", "GET");
          return current.ok ? current : send("auth/refresh", "POST");
        });
      }
      return send("auth/refresh", "POST");
    };
    refreshing ??= rotate().finally(() => { refreshing = undefined; });
    if ((await refreshing).ok) response = await send(path, method, data);
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status}).`;
    const body = await response.json().catch(() => null);
    if (typeof body?.detail === "string") detail = body.detail;
    else if (body) detail = Object.entries(body).map(([key, value]) => `${key}: ${String(value)}`).join(" ");
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}
