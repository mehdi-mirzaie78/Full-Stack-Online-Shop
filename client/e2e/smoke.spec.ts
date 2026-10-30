import { expect, test } from "@playwright/test";

test("storefront renders and language control works", async ({ page, request }) => {
  if (process.env.E2E_API_URL) {
    const health = await request.get(new URL("/api/health/", process.env.E2E_API_URL).href);
    expect(health.status()).toBe(200);
    expect((await health.json()).status).toBe("healthy");
    expect(health.headers()["x-request-id"]).toMatch(/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/);
  }
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "آزمایشگاه متریال" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await page.getByRole("button", { name: "تغییر جهت به چپ‌به‌راست (LTR)", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Material lab", exact: true })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
});

test("global browser failures emit safe JSON once", async ({ page }) => {
  const events: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && message.text().startsWith("{")) events.push(message.text());
  });
  await page.goto("/");
  await page.evaluate(() => {
    window.dispatchEvent(new ErrorEvent("error", { error: new Error("private-browser-token") }));
    window.dispatchEvent(new PromiseRejectionEvent("unhandledrejection", {
      promise: Promise.resolve(), reason: new Error("private-rejection-token"),
    }));
  });
  await expect.poll(() => events.length).toBe(2);
  expect(events.map((line) => JSON.parse(line).event)).toEqual(["browser_error", "unhandled_rejection"]);
  expect(events.join("\n")).not.toMatch(/private-browser-token|private-rejection-token/);
});

test("unsupported WebGL retains fallback and reports one handled failure", async ({ page }) => {
  const events: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && message.text().startsWith("{")) events.push(message.text());
  });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, ...args) {
      if (String(args[0]).startsWith("webgl")) return null;
      return Reflect.apply(original, this, args);
    } as typeof original;
  });
  await page.goto("/");
  await page.getByRole("button", { name: "بارگذاری نمایش سه‌بعدی", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "نمایش سه‌بعدی در دسترس نیست" })).toBeVisible();
  await expect(page.getByRole("img", { name: "نمونه ثابت متریال" })).toBeVisible();
  await expect.poll(() => events.filter((line) => JSON.parse(line).event === "preview_failed").length).toBe(1);
  await expect(page.getByRole("button", { name: "بارگذاری مجدد صفحه برای تلاش دوباره سه‌بعدی" })).toBeVisible();
});
