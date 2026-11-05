"use client";
import { userSchema } from "@/lib/identity/validation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, parseUser, roles, type User } from "@/lib/identity/api";
import { buttonClass, fieldClass, useIdentityLanguage } from "./language";

type Session = { id: string; created_at: string; expires_at: string; revoked_at: string | null };
export default function Users({ actor, identifier }: { actor: User; identifier?: string }) {
  const { t } = useIdentityLanguage();
  const [users, setUsers] = useState<User[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [phone, setPhone] = useState(""); const [role, setRole] = useState<string>("CUSTOMER");
  const [active, setActive] = useState(true); const [archived, setArchived] = useState(false);
  const [search, setSearch] = useState(""); const [page, setPage] = useState(1); const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [message, setMessage] = useState("");
  const writable = actor.role === "SUPERADMIN";
  const load = useCallback(async () => {
    setBusy(true); setError("");
    try {
      if (identifier) {
        const body = await api(`staff/users/${identifier}`) as { user: unknown; sessions: Session[] };
        const user = parseUser(body.user);
        if (!Array.isArray(body.sessions) || body.sessions.some(session => typeof session.id !== "string" || typeof session.expires_at !== "string" || (session.revoked_at !== null && typeof session.revoked_at !== "string"))) throw new Error("Invalid session response.");
        setPhone(user.phone); setRole(user.role); setActive(user.is_active); setArchived(user.is_deleted); setSessions(body.sessions);
      } else {
        const body = await api(`staff/users?page=${page}&search=${encodeURIComponent(search)}`) as { results: unknown[]; next: unknown };
        if (!Array.isArray(body.results)) throw new Error("Invalid users response.");
        setUsers(body.results.map(parseUser)); setMore(Boolean(body.next));
      }
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Request failed."); }
    finally { setBusy(false); }
  }, [identifier, page, search]);
  useEffect(() => { void load(); }, [load]);
  async function save(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const validation = userSchema.safeParse({ phone, role, is_active: active, is_deleted: archived });
      if (!validation.success) { setError(validation.error.issues[0].message); return; }
      if (identifier && !window.confirm(t("Save these account access changes?", "تغییرات دسترسی حساب ذخیره شود؟"))) return;
      await api(identifier ? `staff/users/${identifier}` : "staff/users", identifier ? "PATCH" : "POST", { phone, role, is_active: active, is_deleted: archived });
      setMessage(t("User saved.", "کاربر ذخیره شد.")); await load();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Save failed."); }
    finally { setBusy(false); }
  }
  return <div className="space-y-6">
    <h1 className="text-2xl font-bold">{identifier ? t("User details", "جزئیات کاربر") : t("Users", "کاربران")}</h1>
    {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    {busy && <p role="status">{t("Loading…", "در حال بارگذاری…")}</p>}
    <Button className={buttonClass} disabled={busy} onClick={() => void load()}>{t("Reload", "بارگذاری دوباره")}</Button>
    {!identifier && <>
      <label className="block">{t("Search phone", "جستجوی شماره")}
        <Input className={fieldClass} type="search" dir="ltr" value={search} onChange={event => { setPage(1); setSearch(event.target.value); }} />
      </label>
      {!users.length && !busy && <p>{t("No users found.", "کاربری پیدا نشد.")}</p>}
      <div className="overflow-auto"><table className="w-full text-start"><thead><tr><th>{t("Phone", "تلفن")}</th><th>{t("Role", "نقش")}</th><th>{t("Status", "وضعیت")}</th></tr></thead>
        <tbody>{users.map(user => <tr key={user.id}><td className="py-3"><Link href={`/admin/users/${user.id}`} dir="ltr" className="underline">{user.phone}</Link></td><td>{user.role}</td><td>{user.is_deleted ? t("Archived", "بایگانی") : user.is_active ? t("Active", "فعال") : t("Inactive", "غیرفعال")}</td></tr>)}</tbody></table></div>
      <div className="flex gap-4"><Button className={buttonClass} disabled={busy || page === 1} onClick={() => setPage(page - 1)}>{t("Previous", "قبلی")}</Button><span>{page}</span><Button className={buttonClass} disabled={busy || !more} onClick={() => setPage(page + 1)}>{t("Next", "بعدی")}</Button></div>
    </>}
    {(identifier || writable) && <form noValidate onSubmit={save} className="max-w-lg space-y-4 rounded border p-4">
      <h2 className="text-xl">{identifier ? t("Account", "حساب") : t("Create user", "ایجاد کاربر")}</h2>
      <label className="block">{t("Phone number", "شماره تلفن")}<Input className={fieldClass} dir="ltr" type="tel" minLength={9} maxLength={16} pattern="\+[1-9][0-9]{7,14}" required value={phone} disabled={!writable || busy} onChange={event => setPhone(event.target.value)} /></label>
      <label className="block">{t("Role", "نقش")}<select className={fieldClass} value={role} disabled={!writable || busy} onChange={event => setRole(event.target.value)}>{roles.map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="flex gap-2"><Input className="h-4 w-4 shrink-0" type="checkbox" checked={active} disabled={!writable || busy} onChange={event => setActive(event.target.checked)} />{t("Active", "فعال")}</label>
      {identifier && <label className="flex gap-2"><Input className="h-4 w-4 shrink-0" type="checkbox" checked={archived} disabled={!writable || busy} onChange={event => setArchived(event.target.checked)} />{t("Archived (uncheck to restore)", "بایگانی (برای بازیابی بردارید)")}</label>}
      {writable && <Button type="submit" className={buttonClass} disabled={busy}>{t("Save user", "ذخیره کاربر")}</Button>}
    </form>}
    {identifier && <section className="space-y-3"><h2 className="text-xl">{t("Login sessions", "نشست‌های ورود")}</h2>
      {!sessions.length && <p>{t("No login sessions.", "نشستی وجود ندارد.")}</p>}
      {sessions.map(session => <div key={session.id} className="flex flex-wrap gap-3 rounded border p-3"><span dir="ltr">{session.id} · {session.expires_at}</span><span>{session.revoked_at ? t("Revoked", "لغو شده") : t("Not revoked", "لغو نشده")}</span>
        {writable && !session.revoked_at && <Button className={buttonClass} disabled={busy} onClick={async () => {
          if (!window.confirm(t("Revoke this session?", "این نشست لغو شود؟"))) return;
          setBusy(true); try { await api(`staff/sessions/${session.id}/revoke`, "POST"); await load(); } catch (failure) { setError(failure instanceof Error ? failure.message : "Revocation failed."); } finally { setBusy(false); }
        }}>{t("Revoke session", "لغو نشست")}</Button>}
      </div>)}
    </section>}
  </div>;
}
