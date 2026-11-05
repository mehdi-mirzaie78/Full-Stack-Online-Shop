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
  await page.getByRole("button", { name: "New user", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Create user", exact: true })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "First name", exact: true })).toBeFocused();
  await page.getByRole("textbox", { name: "First name", exact: true }).fill("Sara");
  await page.getByRole("textbox", { name: "Last name", exact: true }).fill("Test");
  await page.getByRole("textbox", { name: "Phone number", exact: true }).fill("+989120000099");
  await page.getByRole("combobox", { name: "Role", exact: true }).selectOption("OPERATOR");
  await page.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Create user", exact: true })).toHaveCount(0);
  await expect(page.getByRole("status").filter({ hasText: "User saved." })).toBeVisible();
  await page.getByRole("link", { name: "+989120000099", exact: true }).click();
  await expect(page.getByRole("heading", { name: "User details", exact: true })).toBeVisible();
  page.on("dialog", dialog => dialog.accept());
  await page.getByRole("combobox", { name: "Role", exact: true }).selectOption("PRODUCT_MANAGER");
  await page.getByRole("switch", { name: "Archived (turn off to restore)", exact: true }).check();
  await page.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "User saved." })).toBeVisible();
  await page.reload();
  // Language preference is local UI state and defaults to Persian on full reload.
  await page.getByRole("button", { name: "English", exact: true }).click();
  await expect(page.getByRole("switch", { name: "Archived (turn off to restore)", exact: true })).toBeChecked();
  await page.getByRole("switch", { name: "Archived (turn off to restore)", exact: true }).uncheck();
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
  await page.getByRole("tab", { name: "Login sessions", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Login sessions", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Revoke session", exact: true })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "Permissions", exact: true })).toHaveCount(0);
  await page.getByRole("tab", { name: "Account", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Phone number", exact: true })).toBeDisabled();
  await expect(page.getByRole("switch", { name: "Active", exact: true })).toBeDisabled();
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

test("mobile staff navigation opens and closes with keyboard support", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, "+989120000002");
  await expect(page).toHaveURL(/\/admin\/users$/);
  const open = page.getByRole("button", { name: "Open navigation", exact: true });
  await open.click();
  await expect(page.getByRole("dialog", { name: "Staff navigation", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(open).toBeFocused();
});

test("reference admin layout supports collapse, appearance and bilingual tables", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 960 });
  await login(page, "+989120000001");
  await expect(page.getByRole("table", { name: "Users", exact: true })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Joined", exact: true })).toBeVisible();
  const workspace = page.locator(".admin-workspace");
  await expect(workspace).toHaveAttribute("data-theme", "light");
  await page.getByRole("button", { name: "Toggle sidebar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Toggle sidebar", exact: true })).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".admin-sidebar")).toHaveCSS("width", "72px");
  await page.getByRole("button", { name: "Use dark theme", exact: true }).click();
  await expect(workspace).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Use light theme", exact: true }).click();
  await page.getByRole("button", { name: "Toggle sidebar", exact: true }).click();
  await page.getByRole("searchbox", { name: "Search phone", exact: true }).fill("000001");
  await expect(page.getByRole("link", { name: "+989120000001", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "+989120000002", exact: true })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Search phone", exact: true }).fill("");
  await expect(page.getByRole("link", { name: "+989120000002", exact: true })).toBeVisible();
  await page.screenshot({ path: "/tmp/shop-admin-reference-desktop.png", fullPage: true });
  await page.getByRole("button", { name: "فارسی", exact: true }).click();
  await expect(workspace).toHaveAttribute("dir", "rtl");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: "باز کردن ناوبری", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.screenshot({ path: "/tmp/shop-admin-reference-mobile.png", fullPage: true });
});


test("creation dialog validates input and restores focus when dismissed", async ({ page }) => {
  await login(page, "+989120000001");
  const trigger = page.getByRole("button", { name: "New user", exact: true });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Create user", exact: true });
  const active = dialog.getByRole("switch", { name: "Active", exact: true });
  await expect(active).toBeChecked();
  await active.focus();
  await page.keyboard.press("Space");
  await expect(active).not.toBeChecked();
  await page.keyboard.press("Space");
  await expect(active).toBeChecked();
  await expect(active.locator("[data-slot=switch-thumb]")).toHaveCSS("transform", "matrix(1, 0, 0, 1, 16, 0)");
  await page.screenshot({ path: "/tmp/shop-admin-switches-create.png", fullPage: true });
  const bounds = await dialog.boundingBox();
  expect(bounds).not.toBeNull();
  expect(Math.abs(bounds!.y + bounds!.height / 2 - page.viewportSize()!.height / 2)).toBeLessThan(2);
  await dialog.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(dialog.getByRole("alert")).toBeVisible();
  await expect(dialog).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
  await trigger.click();
  await expect(dialog.getByRole("alert")).toHaveCount(0);
  await expect(dialog.getByRole("textbox", { name: "Phone number", exact: true })).toHaveValue("");
  await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(trigger).toBeFocused();
});


test("superadmin creates a password account and manages role and individual grants", async ({ page }) => {
  await login(page, "+989120000001");
  await page.getByRole("button", { name: "New user", exact: true }).click();
  const creation = page.getByRole("dialog", { name: "Create user", exact: true });
  await creation.getByRole("textbox", { name: "First name", exact: true }).fill("علی");
  await creation.getByRole("textbox", { name: "Last name", exact: true }).fill("آزمایشی");
  await creation.getByRole("textbox", { name: "Phone number", exact: true }).fill("+989120000088");
  await creation.getByLabel("Password", { exact: true }).fill("Synthetic-Browser-Password-942!");
  await creation.getByLabel("Confirm password", { exact: true }).fill("Synthetic-Browser-Password-942!");
  await creation.getByRole("button", { name: "Save user", exact: true }).click();
  await expect(creation).toHaveCount(0);
  await expect(page.getByRole("link", { name: "+989120000088", exact: true })).toBeVisible();
  page.on("dialog", dialog => dialog.accept());
  await page.getByRole("link", { name: "Roles & permissions", exact: true }).click();
  await page.getByRole("switch", { name: "View users and sessions", exact: true }).check();
  await page.getByRole("button", { name: "فارسی", exact: true }).click();
  const persianSwitch = page.getByRole("switch", { name: "مشاهده کاربران و نشست‌ها", exact: true });
  await expect(persianSwitch).toBeChecked();
  await expect(persianSwitch.locator("[data-slot=switch-thumb]")).toHaveCSS("transform", "matrix(1, 0, 0, 1, -16, 0)");
  await page.screenshot({ path: "/tmp/shop-admin-switches-permissions.png", fullPage: true });
  await page.getByRole("button", { name: "English", exact: true }).click();
  await page.getByRole("button", { name: "Save permissions", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Permissions saved." })).toBeVisible();
  await page.getByRole("link", { name: "Users", exact: true }).click();
  await page.getByRole("link", { name: "+989120000004", exact: true }).click();
  await page.getByRole("tab", { name: "Permissions", exact: true }).click();
  await page.getByRole("switch", { name: "Create customer accounts", exact: true }).check();
  await page.getByRole("button", { name: "Save permissions", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Permissions saved." })).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await login(page, "+989120000004");
  await expect(page).toHaveURL(/\/admin\/users$/);
  await expect(page.getByRole("link", { name: "Roles & permissions", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "New user", exact: true }).click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  const denied = await page.evaluate(async () => (await fetch("http://127.0.0.1:8100/api/v1/staff/access", { credentials: "include" })).status);
  expect(denied).toBe(403);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/login");
  // A full navigation restores the default Persian UI.
  await page.getByRole("button", { name: "English", exact: true }).click();
  await page.getByRole("button", { name: "Password", exact: true }).click();
  await page.getByRole("textbox", { name: "Phone number", exact: true }).fill("+989120000088");
  await page.getByLabel("Password", { exact: true }).fill("Synthetic-Browser-Password-942!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL("http://127.0.0.1:3100/");
});


test("user names persist and edit tabs retain drafts with keyboard and RTL navigation", async ({ page }) => {
  await login(page, "+989120000001");
  await page.getByRole("link", { name: "+989120000001", exact: true }).click();
  const firstName = page.getByRole("textbox", { name: "First name", exact: true });
  await firstName.fill("Tab draft");
  await page.getByRole("tab", { name: "Permissions", exact: true }).click();
  await expect(page.getByRole("tabpanel", { name: "Permissions", exact: true })).toBeVisible();
  await expect(firstName).not.toBeVisible();
  await page.getByRole("tab", { name: "Login sessions", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Login sessions", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Account", exact: true }).click();
  await expect(firstName).toHaveValue("Tab draft");
  const account = page.getByRole("tab", { name: "Account", exact: true });
  await account.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Permissions", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "فارسی", exact: true }).click();
  const permissions = page.getByRole("tab", { name: "مجوزها", exact: true });
  await permissions.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "حساب", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("textbox", { name: "نام", exact: true }).fill("سارا");
  await page.getByRole("textbox", { name: "نام خانوادگی", exact: true }).fill("آزمایشی");
  page.on("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "ذخیره کاربر", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "کاربر ذخیره شد." })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("textbox", { name: "نام", exact: true })).toHaveValue("سارا");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "/tmp/shop-user-tabs-mobile.png", fullPage: true });
});


test("the latest phone filter wins when earlier responses arrive late", async ({ page }) => {
  await login(page, "+989120000001");
  const search = page.getByRole("searchbox", { name: "Search phone", exact: true });
  await expect(page.getByRole("link", { name: "+989120000002", exact: true })).toBeVisible();
  let releaseSlow!: () => void;
  let captureSlow!: () => void;
  const gate = new Promise<void>(resolve => { releaseSlow = resolve; });
  const captured = new Promise<void>(resolve => { captureSlow = resolve; });
  await page.route("**/staff/users?**", async route => {
    const response = await route.fetch();
    if (new URL(route.request().url()).searchParams.get("search") === "00000") {
      captureSlow(); await gate;
    }
    await route.fulfill({ response });
  });
  await search.fill("00000");
  await captured;
  await search.fill("000002");
  await expect(page.getByRole("link", { name: "+989120000001", exact: true })).toHaveCount(0);
  const delayed = page.waitForResponse(response => new URL(response.url()).searchParams.get("search") === "00000");
  releaseSlow();
  await (await delayed).finished();
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(page.getByRole("link", { name: "+989120000002", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "+989120000001", exact: true })).toHaveCount(0);
});


test("revoking a session preserves unsaved account fields in another tab", async ({ page, browser, baseURL }) => {
  await login(page, "+989120000001");
  const auditorContext = await browser.newContext({ baseURL });
  try {
    const auditorPage = await auditorContext.newPage();
    await login(auditorPage, "+989120000002");
    await expect(auditorPage).toHaveURL(/\/admin\/users$/);
    await page.getByRole("link", { name: "+989120000002", exact: true }).click();
    await page.getByRole("textbox", { name: "First name", exact: true }).fill("Unsaved account name");
    await page.getByRole("tab", { name: "Login sessions", exact: true }).click();
    page.on("dialog", dialog => dialog.accept());
    const refreshed = page.waitForResponse(response => response.request().method() === "GET" && /\/staff\/users\/[\w-]+$/.test(new URL(response.url()).pathname));
    await page.getByRole("button", { name: "Revoke session", exact: true }).first().click();
    await refreshed;
    await expect(page.getByRole("button", { name: "Reload", exact: true })).toBeEnabled();
    await page.getByRole("tab", { name: "Account", exact: true }).click();
    await expect(page.getByRole("textbox", { name: "First name", exact: true })).toHaveValue("Unsaved account name");
  } finally { await auditorContext.close(); }
});
