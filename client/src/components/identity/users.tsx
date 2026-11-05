"use client";
import { staffPasswordSchema, userSchema } from "@/lib/identity/validation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DirectionProvider } from "@base-ui/react/direction-provider";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Plus, RotateCw, Search, ShieldCheck, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, canManageIdentity, parseUser, roles, type User } from "@/lib/identity/api";
import PermissionSettings from "./permission-settings";
import { useIdentityLanguage } from "./language";

type Session = { id: string; created_at: string; expires_at: string; revoked_at: string | null };
export default function Users({ actor, identifier }: { actor: User; identifier?: string }) {
  const { t, persian } = useIdentityLanguage();
  const [accessVersion, setAccessVersion] = useState(0);
  const [password, setPassword] = useState(""); const [confirmPassword, setConfirmPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const creationDialog = useRef<HTMLDialogElement>(null);
  const firstNameInput = useRef<HTMLInputElement>(null);
  const loadSequence = useRef(0);
  const [users, setUsers] = useState<User[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [firstName, setFirstName] = useState(""); const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState(""); const [role, setRole] = useState<string>("CUSTOMER");
  const [active, setActive] = useState(true); const [archived, setArchived] = useState(false);
  const [search, setSearch] = useState(""); const [page, setPage] = useState(1); const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [message, setMessage] = useState("");
  const superadmin = actor.role === "SUPERADMIN";
  const writable = canManageIdentity(actor, identifier ? "change_user" : "add_user") && (superadmin || role === "CUSTOMER");
  const load = useCallback(async ({ preserveAccount = false }: { preserveAccount?: boolean } = {}) => {
    const sequence = ++loadSequence.current;
    setBusy(true); setError("");
    try {
      if (identifier) {
        const body = await api(`staff/users/${identifier}`) as { user: unknown; sessions: Session[] };
        const user = parseUser(body.user);
        if (!Array.isArray(body.sessions) || body.sessions.some(session => typeof session.id !== "string" || typeof session.expires_at !== "string" || (session.revoked_at !== null && typeof session.revoked_at !== "string"))) throw new Error("Invalid session response.");
        if (sequence !== loadSequence.current) return;
        if (!preserveAccount) {
          setFirstName(user.first_name); setLastName(user.last_name); setPhone(user.phone); setRole(user.role); setActive(user.is_active); setArchived(user.is_deleted);
        }
        setSessions(body.sessions);
      } else {
        const body = await api(`staff/users?page=${page}&search=${encodeURIComponent(search)}`) as { results: unknown[]; next: unknown };
        if (!Array.isArray(body.results)) throw new Error("Invalid users response.");
        const results = body.results.map(parseUser);
        if (sequence !== loadSequence.current) return;
        setUsers(results); setMore(Boolean(body.next));
      }
    } catch (failure) { if (sequence === loadSequence.current) setError(failure instanceof Error ? failure.message : "Request failed."); }
    finally { if (sequence === loadSequence.current) setBusy(false); }
  }, [identifier, page, search]);
  useEffect(() => { void load(); return () => { loadSequence.current += 1; }; }, [load]);
  async function save(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const validation = userSchema.safeParse({ first_name: firstName, last_name: lastName, phone, role, is_active: active, is_deleted: archived });
      if (!validation.success) { setError(validation.error.issues[0].message); return; }
      const passwordValidation = staffPasswordSchema.safeParse({ password, confirmPassword });
      if (!passwordValidation.success) { setError(passwordValidation.error.issues[0].message); return; }
      if (identifier && !window.confirm(t("Save these account access changes?", "تغییرات دسترسی حساب ذخیره شود؟"))) return;
      await api(identifier ? `staff/users/${identifier}` : "staff/users", identifier ? "PATCH" : "POST", { ...validation.data, ...(superadmin && password ? { password } : {}) });
      setPassword(""); setConfirmPassword("");
      setMessage(t("User saved.", "کاربر ذخیره شد."));
      if (!identifier) creationDialog.current?.close();
      else setAccessVersion(value => value + 1);
      await load();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Save failed."); }
    finally { setBusy(false); }
  }
  const editor = <form id="user-editor" noValidate onSubmit={save} className="max-w-lg space-y-4 rounded border p-4">
      {identifier && <h2 className="text-xl">{t("Account", "حساب")}</h2>}
      {!identifier && error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      <label className={identifier ? "block" : "admin-dialog-field"}>{t("First name", "نام")}<Input ref={firstNameInput} className="admin-field" autoComplete="given-name" autoFocus={!identifier} maxLength={150} required value={firstName} disabled={!writable || busy} onChange={event => setFirstName(event.target.value)} /></label>
      <label className={identifier ? "block" : "admin-dialog-field"}>{t("Last name", "نام خانوادگی")}<Input className="admin-field" autoComplete="family-name" maxLength={150} required value={lastName} disabled={!writable || busy} onChange={event => setLastName(event.target.value)} /></label>
      <label className={identifier ? "block" : "admin-dialog-field"}>{t("Phone number", "شماره تلفن")}<Input className="admin-field" dir="ltr" type="tel" placeholder="+989121234567" minLength={9} maxLength={16} pattern="\+[1-9][0-9]{7,14}" required value={phone} disabled={!writable || busy} onChange={event => setPhone(event.target.value)} /></label>
      <label className={identifier ? "block" : "admin-dialog-field"}>{t("Role", "نقش")}<select className="admin-field" value={role} disabled={!writable || busy} onChange={event => setRole(event.target.value)}>{(superadmin ? roles : ["CUSTOMER"]).map(value => <option key={value}>{value}</option>)}</select></label>
      {superadmin && <>
        <label className={identifier ? "block" : "admin-dialog-field"}>{t("Password", "رمز عبور")}<Input className="admin-field" dir="ltr" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={password} disabled={busy} onChange={event => setPassword(event.target.value)} /></label>
        <label className={identifier ? "block" : "admin-dialog-field"}>{t("Confirm password", "تکرار رمز عبور")}<Input className="admin-field" dir="ltr" type="password" autoComplete="new-password" maxLength={128} value={confirmPassword} disabled={busy} onChange={event => setConfirmPassword(event.target.value)} /></label>
        <p className="text-xs text-muted-foreground">{identifier ? t("Leave blank to keep the current password. Setting a password signs this account out of all sessions.", "برای حفظ رمز فعلی خالی بگذارید. تنظیم رمز، همه نشست‌های این حساب را لغو می‌کند.") : t("Optional. Leave blank for an account without password sign-in. Use at least 8 characters; common or entirely numeric passwords are rejected.", "اختیاری است. برای حساب بدون ورود با رمز خالی بگذارید. حداقل ۸ نویسه؛ رمزهای رایج یا کاملاً عددی پذیرفته نمی‌شوند.")}</p>
      </>}
      <label className={identifier ? "flex items-center gap-3" : "admin-dialog-toggle"}><Switch checked={active} disabled={!writable || busy} onCheckedChange={setActive} />{t("Active", "فعال")}</label>
      {identifier && <label className="flex items-center gap-3"><Switch checked={archived} disabled={!writable || busy} onCheckedChange={setArchived} />{t("Archived (turn off to restore)", "بایگانی (برای بازیابی خاموش کنید)")}</label>}
      <div className="admin-editor-actions">{!identifier && <Button type="button" variant="outline" disabled={busy} onClick={() => creationDialog.current?.close()}>{t("Cancel", "انصراف")}</Button>}{writable && <Button type="submit" disabled={busy}>{t("Save user", "ذخیره کاربر")}</Button>}</div>
    </form>;
  return <div className="admin-users space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-semibold">{identifier ? t("User details", "جزئیات کاربر") : t("Users", "کاربران")}</h1><p className="mt-1 text-sm text-muted-foreground">{t("Manage account access and review login sessions.", "دسترسی حساب‌ها و نشست‌های ورود را مدیریت کنید.")}</p></div><div className="flex items-center gap-3"><Button variant="outline" disabled={busy} onClick={() => void load()}><RotateCw size={16} />{t("Reload", "بارگذاری دوباره")}</Button>{!identifier && writable && <Button disabled={busy} aria-haspopup="dialog" aria-expanded={creating} aria-controls="create-user-dialog" onClick={() => { setPassword(""); setConfirmPassword(""); setFirstName(""); setLastName(""); setPhone(""); setRole("CUSTOMER"); setActive(true); setArchived(false); setError(""); setMessage(""); setCreating(true); creationDialog.current?.showModal(); firstNameInput.current?.focus(); }}><Plus size={16} />{t("New user", "کاربر جدید")}</Button>}</div></div>
    {error && !creating && <p role="alert" className="text-sm text-destructive">{error}</p>}{message && <p role="status" className="text-sm text-muted-foreground">{message}</p>}
    {busy && <p role="status">{t("Loading…", "در حال بارگذاری…")}</p>}
    {!identifier && <>
      <div className="admin-table-toolbar">
        <label className="admin-search"><span className="sr-only">{t("Search phone", "جستجوی شماره")}</span><Search size={16} aria-hidden="true" />
          <Input type="search" dir="ltr" placeholder={t("Filter phone numbers…", "جستجوی شماره تلفن…")} value={search} onChange={event => { setPage(1); setSearch(event.target.value); }} />
        </label>
        <span className="text-xs text-muted-foreground">{t("Account access & roles", "دسترسی و نقش حساب‌ها")}</span>
      </div>
      <div className="admin-table-container"><table aria-label={t("Users", "کاربران")} aria-busy={busy} className="w-full text-start"><thead><tr><th scope="col">{t("Name", "نام")}</th><th scope="col">{t("Phone", "تلفن")}</th><th scope="col">{t("Status", "وضعیت")}</th><th scope="col">{t("Role", "نقش")}</th><th scope="col">{t("Joined", "تاریخ عضویت")}</th><th scope="col"><span className="sr-only">{t("Actions", "عملیات")}</span></th></tr></thead>
        <tbody>{users.map(user => <tr key={user.id}>
          <td>{[user.first_name, user.last_name].filter(Boolean).join(" ") || <span className="text-muted-foreground">{t("Name needed", "نام ثبت نشده")}</span>}</td>
          <td><Link href={`/admin/users/${user.id}`} dir="ltr" className="admin-phone">{user.phone}</Link></td>
          <td><span className="admin-status" data-status={user.is_deleted ? "archived" : user.is_active ? "active" : "inactive"}>{user.is_deleted ? t("Archived", "بایگانی") : user.is_active ? t("Active", "فعال") : t("Inactive", "غیرفعال")}</span></td>
          <td><span className="admin-role"><ShieldCheck size={15} aria-hidden="true" />{({ SUPERADMIN: t("Superadmin", "مدیر کل"), PRODUCT_MANAGER: t("Product manager", "مدیر محصول"), OPERATOR: t("Operator", "اپراتور"), AUDITOR: t("Auditor", "حسابرس"), CUSTOMER: t("Customer", "مشتری") })[user.role]}</span></td>
          <td className="text-muted-foreground"><time dateTime={user.created_at}>{new Date(user.created_at).toLocaleDateString(persian ? "fa-IR" : "en-US", { year: "numeric", month: "short", day: "numeric" })}</time></td>
          <td><Link className="admin-row-action" href={`/admin/users/${user.id}`} aria-label={`${t("View account", "مشاهده حساب")} ${user.phone}`}>{t("Details", "جزئیات")}</Link></td>
        </tr>)}{!users.length && <tr><td colSpan={6} className="admin-empty">{busy ? t("Loading…", "در حال بارگذاری…") : error ? t("Unable to load users. Try Reload.", "بارگذاری کاربران ناموفق بود. دوباره تلاش کنید.") : t("No users found.", "کاربری پیدا نشد.")}</td></tr>}</tbody></table></div>
      <div className="admin-pagination"><span className="text-sm text-muted-foreground">{t(`${users.length} accounts on this page`, `${users.length.toLocaleString("fa-IR")} حساب در این صفحه`)}</span><div className="flex items-center gap-3"><span className="text-sm" aria-live="polite">{t(`Page ${page}`, `صفحه ${page.toLocaleString("fa-IR")}`)}</span><Button variant="outline" disabled={busy || page === 1} onClick={() => setPage(page - 1)}><ChevronLeft size={16} className="rtl:rotate-180" />{t("Previous", "قبلی")}</Button><Button variant="outline" disabled={busy || !more} onClick={() => setPage(page + 1)}>{t("Next", "بعدی")}<ChevronRight size={16} className="rtl:rotate-180" /></Button></div></div>
    </>}
    {!identifier && writable && <dialog id="create-user-dialog" ref={creationDialog} className="admin-create-dialog" aria-labelledby="create-user-title" aria-describedby="create-user-description" dir={persian ? "rtl" : "ltr"} onCancel={event => { if (busy) event.preventDefault(); }} onClose={() => { setCreating(false); setError(""); setPassword(""); setConfirmPassword(""); }}>
      <div className="admin-dialog-heading"><h2 id="create-user-title">{t("Create user", "ایجاد کاربر")}</h2><Button type="button" variant="ghost" size="icon" disabled={busy} aria-label={t("Close form", "بستن فرم")} onClick={() => creationDialog.current?.close()}><X size={16} /></Button></div>
      <p id="create-user-description" className="text-sm text-muted-foreground">{t("Create an account and assign its access. Click save when you’re done.", "حسابی ایجاد کرده و دسترسی آن را تعیین کنید. سپس ذخیره را بزنید.")}</p>
      {editor}
    </dialog>}
    {identifier && <DirectionProvider direction={persian ? "rtl" : "ltr"}><Tabs defaultValue="account">
      <TabsList aria-label={t("User sections", "بخش‌های کاربر")} activateOnFocus>
        <TabsTrigger value="account">{t("Account", "حساب")}</TabsTrigger>
        {superadmin && <TabsTrigger value="permissions">{t("Permissions", "مجوزها")}</TabsTrigger>}
        <TabsTrigger value="sessions">{t("Login sessions", "نشست‌های ورود")}</TabsTrigger>
      </TabsList>
      <TabsContent value="account" keepMounted>{editor}</TabsContent>
      {superadmin && <TabsContent value="permissions" keepMounted><PermissionSettings key={accessVersion} userId={identifier} /></TabsContent>}
      <TabsContent value="sessions" keepMounted><section className="space-y-3"><h2 className="text-xl">{t("Login sessions", "نشست‌های ورود")}</h2>
      {!sessions.length && <p>{t("No login sessions.", "نشستی وجود ندارد.")}</p>}
      {sessions.map(session => <div key={session.id} className="flex flex-wrap gap-3 rounded border p-3"><span dir="ltr" className="min-w-0 break-all">{session.id} · {session.expires_at}</span><span>{session.revoked_at ? t("Revoked", "لغو شده") : t("Not revoked", "لغو نشده")}</span>
        {canManageIdentity(actor, "revoke_loginsession") && (superadmin || role === "CUSTOMER") && !session.revoked_at && <Button variant="outline" disabled={busy} onClick={async () => {
          if (!window.confirm(t("Revoke this session?", "این نشست لغو شود؟"))) return;
          setBusy(true); try { await api(`staff/sessions/${session.id}/revoke`, "POST"); await load({ preserveAccount: true }); } catch (failure) { setError(failure instanceof Error ? failure.message : "Revocation failed."); } finally { setBusy(false); }
        }}>{t("Revoke session", "لغو نشست")}</Button>}
      </div>)}
    </section></TabsContent>
    </Tabs></DirectionProvider>}
  </div>;
}
