"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { ArrowLeft, LayoutDashboard, LogOut, Menu, Moon, PanelLeft, ShieldCheck, Sun, Users, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, canManageIdentity, type User } from "@/lib/identity/api";
import { LanguageToggle, useIdentityLanguage } from "./language";

function StaffNavigation({ user, close }: { user: User; close?: () => void }) {
  const { t } = useIdentityLanguage(); const path = usePathname();
  return <>
    <Link href="/admin" className="admin-brand" title={t("Shop workspace", "پنل فروشگاه")} onClick={close}><span className="admin-brand-icon"><ShieldCheck size={20} /></span><span>{t("Shop workspace", "پنل فروشگاه")}<small>{t("Administration", "مدیریت")}</small></span></Link>
    <p className="admin-nav-label">{t("Workspace", "فضای کاری")}</p>
    <nav aria-label={t("Staff navigation", "ناوبری مدیریت")} className="space-y-1">
      {!canManageIdentity(user) && <Link className="admin-nav-link" title={t("Overview", "نمای کلی")} aria-current={path === "/admin" ? "page" : undefined} href="/admin" onClick={close}><LayoutDashboard size={18} /><span>{t("Overview", "نمای کلی")}</span></Link>}
      {canManageIdentity(user) && <Link className="admin-nav-link" title={t("Users", "کاربران")} aria-current={path.startsWith("/admin/users") ? "page" : undefined} href="/admin/users" onClick={close}><Users size={18} /><span>{t("Users", "کاربران")}</span></Link>}
      {user.role === "SUPERADMIN" && <Link className="admin-nav-link" title={t("Roles & permissions", "نقش‌ها و مجوزها")} aria-current={path.startsWith("/admin/permissions") ? "page" : undefined} href="/admin/permissions" onClick={close}><ShieldCheck size={18} /><span>{t("Roles & permissions", "نقش‌ها و مجوزها")}</span></Link>}
    </nav>
    <div className="admin-sidebar-footer"><Link href="/" className="admin-nav-link" title={t("Back to storefront", "بازگشت به فروشگاه")}><ArrowLeft size={18} className="rtl:rotate-180" /><span>{t("Back to storefront", "بازگشت به فروشگاه")}</span></Link><div className="admin-account"><span className="admin-avatar"><Users size={16} /></span><span><strong dir="ltr">{user.phone}</strong><small>{user.role.replaceAll("_", " ")}</small></span></div></div>
  </>;
}

export default function StaffShell({ user, children }: { user: User; children: React.ReactNode }) {
  const { t, persian } = useIdentityLanguage(); const router = useRouter(); const path = usePathname();
  const [collapsed, setCollapsed] = useState(false); const [dark, setDark] = useState(false);
  const menu = useRef<HTMLDialogElement>(null); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function signOut() {
    setBusy(true);
    try { await api("auth/logout", "POST"); router.replace("/login"); router.refresh(); }
    catch { setError(t("Sign-out failed. Please retry.", "خروج ناموفق بود. دوباره تلاش کنید.")); }
    finally { setBusy(false); }
  }
  return <div className="admin-workspace" data-collapsed={collapsed} data-theme={dark ? "dark" : "light"} dir={persian ? "rtl" : "ltr"}>
    <aside className="admin-sidebar hidden md:flex"><StaffNavigation user={user} /></aside>
    <dialog aria-label={t("Staff navigation", "ناوبری مدیریت")} ref={menu} className="admin-mobile-menu" dir={persian ? "rtl" : "ltr"}>
      <Button variant="ghost" className="self-end" aria-label={t("Close navigation", "بستن ناوبری")} onClick={() => menu.current?.close()}><X size={18} /></Button>
      <StaffNavigation user={user} close={() => menu.current?.close()} />
    </dialog>
    <div className="admin-inset">
      <header dir="ltr" className="admin-topbar">
        <div className="flex items-center gap-3"><Button variant="ghost" className="md:hidden" aria-label={t("Open navigation", "باز کردن ناوبری")} onClick={() => menu.current?.showModal()}><Menu size={20} /></Button><Button variant="ghost" className="hidden md:inline-flex" aria-label={t("Toggle sidebar", "تغییر نوار کناری")} aria-expanded={!collapsed} onClick={() => setCollapsed(value => !value)}><PanelLeft size={18} /></Button><span dir={persian ? "rtl" : "ltr"} className="admin-breadcrumb">{t("Workspace", "فضای کاری")} / <span className="text-foreground">{path.includes("/permissions") ? t("Permissions", "مجوزها") : path.includes("/users") ? t("Users", "کاربران") : t("Overview", "نمای کلی")}</span></span></div>
        <div className="flex items-center gap-3"><LanguageToggle /><Button variant="ghost" size="icon" aria-label={dark ? t("Use light theme", "پوسته روشن") : t("Use dark theme", "پوسته تیره")} onClick={() => setDark(value => !value)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</Button><Button variant="ghost" disabled={busy} onClick={signOut} aria-label={t("Sign out", "خروج")}><LogOut size={18} /><span className="hidden sm:inline">{t("Sign out", "خروج")}</span></Button></div>
      </header>
      <main className="admin-content">{error && <p role="alert" className="mb-4 text-destructive">{error}</p>}{children}</main>
    </div>
  </div>;
}
export function StaffWelcome() {
  const { t } = useIdentityLanguage();
  return <section><h1 className="text-2xl font-semibold">{t("Your workspace", "فضای کاری شما")}</h1><p className="mt-2 text-muted-foreground">{t("Your account is signed in. No tools are available for this role yet.", "وارد حساب شدید. هنوز ابزاری برای این نقش ارائه نشده است.")}</p></section>;
}
