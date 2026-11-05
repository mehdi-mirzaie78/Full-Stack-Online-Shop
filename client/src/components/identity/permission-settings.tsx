"use client";
import { useCallback, useEffect, useState } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { api, roles } from "@/lib/identity/api";
import { useIdentityLanguage } from "./language";

const permissionCode = z.enum(["view_user", "add_user", "change_user", "revoke_loginsession"]);
const permissionList = z.array(permissionCode);
const catalogSchema = z.object({
  permissions: z.array(z.object({ codename: permissionCode, label: z.string() })),
  roles: z.array(z.object({ role: z.enum(roles), permissions: permissionList })),
});
const userAccessSchema = z.object({ role: z.enum(roles), permissions: permissionList, inherited: permissionList, effective: permissionList });
type Catalog = z.infer<typeof catalogSchema>;

export default function PermissionSettings({ userId }: { userId?: string }) {
  const { t } = useIdentityLanguage();
  const [loadFailed, setLoadFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const [catalog, setCatalog] = useState<Catalog>();
  const [role, setRole] = useState<string>("OPERATOR");
  const [selected, setSelected] = useState<string[]>([]); const [expected, setExpected] = useState<string[]>([]);
  const [inherited, setInherited] = useState<string[]>([]); const [effective, setEffective] = useState<string[]>([]);
  const [busy, setBusy] = useState(true); const [error, setError] = useState(""); const [message, setMessage] = useState("");
  const roleToLoad = userId ? undefined : role;
  const load = useCallback(async () => {
    setBusy(true); setReady(false); setLoadFailed(false); setError("");
    try {
      const next = catalogSchema.parse(await api("staff/access")); setCatalog(next);
      if (userId) {
        const access = userAccessSchema.parse(await api(`staff/users/${userId}/permissions`));
        setRole(access.role); setSelected(access.permissions); setExpected(access.permissions);
        setInherited(access.inherited); setEffective(access.effective);
      } else {
        const permissions = next.roles.find(item => item.role === roleToLoad)?.permissions;
        if (!permissions) throw new Error("Role is unavailable.");
        setSelected(permissions); setExpected(permissions);
      }
      setReady(true);
    } catch { setLoadFailed(true); }
    finally { setBusy(false); }
  }, [userId, roleToLoad]);
  useEffect(() => { void load(); }, [load]);
  const fixed = role === "SUPERADMIN" || role === "CUSTOMER";
  const labels: Record<string, string> = {
    view_user: t("View users and sessions", "مشاهده کاربران و نشست‌ها"),
    add_user: t("Create customer accounts", "ایجاد حساب مشتری"),
    change_user: t("Edit customer accounts", "ویرایش حساب مشتری"),
    revoke_loginsession: t("Revoke customer sessions", "لغو نشست‌های مشتری"),
  };
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!window.confirm(t("Save these permission changes?", "تغییرات مجوزها ذخیره شود؟"))) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await api(userId ? `staff/users/${userId}/permissions` : `staff/roles/${role}/permissions`, "PATCH", { permissions: selected, expected_permissions: expected });
      await load(); setMessage(t("Permissions saved.", "مجوزها ذخیره شدند."));
    } catch (failure) { setError(failure instanceof Error ? failure.message : t("Save failed.", "ذخیره ناموفق بود.")); }
    finally { setBusy(false); }
  }
  return <section className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">{userId ? t("User permissions", "مجوزهای کاربر") : t("Role permissions", "مجوزهای نقش")}</h2><Button variant="outline" disabled={busy} onClick={() => void load()}>{t("Reload permissions", "بارگذاری مجوزها")}</Button></div>
    <p className="max-w-2xl text-sm text-muted-foreground">{t("Individual grants add to role permissions. User editing requires both view and edit access. Only superadmins can set passwords, assign staff roles, or change permissions. Auditors remain read-only; customer accounts cannot enter the staff panel.", "مجوزهای فردی به مجوزهای نقش اضافه می‌شوند. ویرایش کاربر نیازمند مجوز مشاهده و ویرایش است. فقط مدیر کل می‌تواند رمز عبور، نقش کارکنان و مجوزها را تغییر دهد. حسابرس فقط دسترسی خواندن دارد و مشتری وارد پنل مدیریت نمی‌شود.")}</p>
    {loadFailed && <p role="alert" className="text-sm text-destructive">{t("Could not load permissions. Reload to retry.", "مجوزها بارگذاری نشدند. دوباره تلاش کنید.")}</p>}
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}{message && <p role="status">{message}</p>}
    {busy && <p role="status">{t("Loading permissions…", "در حال بارگذاری مجوزها…")}</p>}
    {!userId && <label className="block max-w-sm text-sm">{t("Role", "نقش")}<select className="admin-field" disabled={busy} value={role} onChange={event => { setMessage(""); setRole(event.target.value); }}>{roles.map(value => <option key={value}>{value}</option>)}</select></label>}
    {userId && <div className="space-y-2 text-sm text-muted-foreground"><p>{t("Inherited from role", "ارث‌برده از نقش")}: {inherited.map(code => labels[code]).join("، ") || t("None", "هیچ‌کدام")}</p><p>{t("Effective access", "دسترسی مؤثر")}: {effective.map(code => labels[code]).join("، ") || t("None", "هیچ‌کدام")}</p></div>}
    {fixed && <p className="text-sm">{t("This role has fixed access and cannot receive individual overrides.", "دسترسی این نقش ثابت است و مجوز فردی نمی‌پذیرد.")}</p>}
    <form onSubmit={save} className="max-w-2xl space-y-4 border">
      <fieldset disabled={busy || fixed || !ready} className="space-y-3"><legend className="mb-3 font-medium">{userId ? t("Additional user grants", "مجوزهای افزوده کاربر") : t("Granted to this role", "مجوزهای این نقش")}</legend>
        {catalog?.permissions.map(permission => <label key={permission.codename} className="flex items-center gap-3 text-sm"><Switch checked={selected.includes(permission.codename)} disabled={busy || fixed || !ready || (role === "AUDITOR" && permission.codename !== "view_user")} onCheckedChange={checked => setSelected(current => checked ? [...current, permission.codename] : current.filter(code => code !== permission.codename))} />{labels[permission.codename]}</label>)}
      </fieldset>
      {!fixed && <Button type="submit" disabled={busy || !ready}>{t("Save permissions", "ذخیره مجوزها")}</Button>}
    </form>
  </section>;
}
