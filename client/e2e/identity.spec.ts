import { execFileSync } from "node:child_process";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

const server = path.resolve(__dirname, "../../server");
function fixture(...args: string[]): string {
  if (!process.env.TEST_PYTHON || process.env.SHOP_TEST_MODE !== "1") throw new Error("Identity E2E requires the isolated root runner.");
  return execFileSync(process.env.TEST_PYTHON, ["manage.py", "test_identity", ...args], {
    cwd: server, env: { ...process.env, DJANGO_SETTINGS_MODULE: "config.test_settings" }, encoding: "utf8",
  }).trim();
}
async function login(page: Page, phone: string) {
  await page.goto("/login");
  await page.getByRole("button", { name: "English", exact: true }).focus();
  await page.keyboard.press("Enter");
  await page.getByRole("textbox", { name: "Phone number", exact: true }).fill(phone);
  await page.getByRole("button", { name: "Send code", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Verification code", exact: true })).toBeVisible();
  await page.getByRole("textbox", { name: "Verification code", exact: true }).fill(fixture("code", "--phone", phone));
  await page.getByRole("button", { name: "Verify code", exact: true }).click();
}

test.beforeEach(() => { fixture("reset"); });

test("superadmin manages account access through protected staff screens", async ({ page }) => {
  await login(page, "+989120000001");
  await expect(page).toHaveURL(/\/admin\/users$/);
  await page.getByRole("textbox", { name: "Phone number", exact: true }).fill("+989120000099");
  await page.getByRole("combobox", { name: "Role", exact: true }).selectOption("OPERATOR");
  await page.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "User saved." })).toBeVisible();
  await page.getByRole("link", { name: "+989120000099", exact: true }).click();
  await expect(page.getByRole("heading", { name: "User details", exact: true })).toBeVisible();
  page.on("dialog", dialog => dialog.accept());
  await page.getByRole("combobox", { name: "Role", exact: true }).selectOption("PRODUCT_MANAGER");
  await page.getByRole("checkbox", { name: "Archived (uncheck to restore)", exact: true }).check();
  await page.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "User saved." })).toBeVisible();
  await page.reload();
  // Language preference is local UI state and defaults to Persian on full reload.
  await page.getByRole("button", { name: "English", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: "Archived (uncheck to restore)", exact: true })).toBeChecked();
  await page.getByRole("checkbox", { name: "Archived (uncheck to restore)", exact: true }).uncheck();
  await page.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "User saved." })).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/admin/users");
  await expect(page).toHaveURL(/\/login$/);
});

test("auditor can inspect identities but cannot create accounts", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, "+989120000002");
  await expect(page).toHaveURL(/\/admin\/users$/);
  await expect(page.getByRole("heading", { name: "Create user", exact: true })).toHaveCount(0);
  await page.getByRole("link", { name: "+989120000002", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Login sessions", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Revoke session", exact: true })).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "Phone number", exact: true })).toBeDisabled();
  const status = await page.evaluate(async () => {
    const base = "http://127.0.0.1:8100/api/v1";
    const csrf = await (await fetch(`${base}/auth/csrf`, { credentials: "include" })).json();
    return (await fetch(`${base}/staff/users`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf.csrfToken }, body: JSON.stringify({ phone: "+989120000098" }) })).status;
  });
  expect(status).toBe(403);
  await page.getByRole("button", { name: "فارسی", exact: true }).click();
  await expect(page.getByRole("heading", { name: "جزئیات کاربر", exact: true })).toBeVisible();
});

test("customer login cannot enter staff routes", async ({ page }) => {
  await login(page, "+989120000003");
  await expect(page).toHaveURL("http://127.0.0.1:3100/");
  await page.goto("/admin/users");
  await expect(page).toHaveURL("http://127.0.0.1:3100/");
});

test("refresh cookie restores an expired access session", async ({ page, context }) => {
  await login(page, "+989120000002");
  await expect(page).toHaveURL(/\/admin\/users$/);
  const cookies = await context.cookies();
  await context.clearCookies();
  await context.addCookies(cookies.filter(cookie => cookie.name !== "shop_access"));
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/admin\/users$/);
});

test("navbar anchors stay fixed when changing direction", async ({ page }) => {
  await page.goto("/login");
  const toggle = page.getByRole("button", { name: "English", exact: true });
  const before = await toggle.boundingBox();
  await toggle.click();
  const after = await page.getByRole("button", { name: "فارسی", exact: true }).boundingBox();
  expect(before).not.toBeNull(); expect(after).not.toBeNull();
  expect(Math.abs(before!.x - after!.x)).toBeLessThan(1);
  await expect(page.getByText("وضعیت سرور:")).toHaveCount(0);
});

test("password sign-in reaches the staff workspace without an OTP", async ({ page }) => {
  fixture("seed");
  await page.goto("/login");
  await page.getByRole("button", { name: "English", exact: true }).click();
  await page.getByRole("button", { name: "Password", exact: true }).click();
  await page.getByRole("textbox", { name: "Phone number", exact: true }).fill("+989120000001");
  await page.getByLabel("Password", { exact: true }).fill("isolated-browser-test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/users$/);
  await expect(page.getByRole("heading", { name: "Users", exact: true })).toBeVisible();
  await page.screenshot({ path: "/tmp/shop-shadcn-admin.png", fullPage: true });
});
