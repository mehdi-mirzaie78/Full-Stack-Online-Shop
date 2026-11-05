import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, parseUser } from "./api";

beforeEach(() => vi.stubGlobal("navigator", undefined));
afterEach(() => vi.unstubAllGlobals());
const user = { id: "id", phone: "+989121234567", role: "CUSTOMER", is_active: true, is_deleted: false, created_at: "now" };
describe("identity response boundaries", () => {
  it("rejects malformed user and role projections", () => {
    expect(parseUser(user)).toEqual(user);
    for (const body of [null, {}, { ...user, role: "OWNER" }, { ...user, is_active: "true" }]) {
      expect(() => parseUser(body)).toThrow("Invalid user response");
    }
  });
  it("sends CSRF and credentialed cookies on writes without storing JWTs", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(Response.json({ csrfToken: "masked-test-csrf" }))
      .mockResolvedValueOnce(Response.json({ detail: "Code sent." }, { status: 202 }));
    vi.stubGlobal("fetch", fetcher);
    await api("auth/otp/request", "POST", { phone: user.phone });
    expect(fetcher.mock.calls[1][1]).toMatchObject({ credentials: "include", headers: { "X-CSRFToken": "masked-test-csrf" } });
    expect(fetcher.mock.calls[1][1].body).toBe(JSON.stringify({ phone: user.phone }));
  });
  it("refuses writes when CSRF cannot be established", async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json({}, { status: 503 }));
    vi.stubGlobal("fetch", fetcher);
    await expect(api("auth/logout", "POST")).rejects.toThrow("Cannot establish a secure request");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("rotates refresh cookies once before retrying an expired access request", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(Response.json({}, { status: 401 }))
      .mockResolvedValueOnce(Response.json({ csrfToken: "masked-test-csrf" }))
      .mockResolvedValueOnce(Response.json({ detail: "Signed in." }))
      .mockResolvedValueOnce(Response.json(user));
    vi.stubGlobal("fetch", fetcher);
    expect(await api("auth/me")).toEqual(user);
    expect(fetcher.mock.calls[2][0]).toMatch(/\/auth\/refresh$/);
    expect(fetcher).toHaveBeenCalledTimes(4);
  });
});

it("rechecks cookies inside the browser lock before rotating another tab's session", async () => {
  const request = vi.fn(async (_name: string, callback: () => Promise<Response>) => callback());
  vi.stubGlobal("navigator", { locks: { request } });
  const fetcher = vi.fn().mockResolvedValueOnce(Response.json({}, { status: 401 }))
    .mockResolvedValueOnce(Response.json(user)).mockResolvedValueOnce(Response.json(user));
  vi.stubGlobal("fetch", fetcher);
  expect(await api("auth/me")).toEqual(user);
  expect(request).toHaveBeenCalledOnce();
  expect(fetcher.mock.calls.every(([url]) => String(url).endsWith("/auth/me"))).toBe(true);
});
