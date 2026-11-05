"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, type User } from "@/lib/identity/api";
import { buttonClass, useIdentityLanguage } from "./language";
export default function StaffShell({ user, children }: { user: User; children: React.ReactNode }) {
  const { t } = useIdentityLanguage(); const router = useRouter(); const [error, setError] = useState("");
  return <div className="grid gap-6 md:grid-cols-[15rem_minmax(0,1fr)]">
    <aside><nav aria-label={t("Staff navigation", "ناوبری مدیریت")} className="flex flex-col items-start gap-4 rounded border p-4">
      <Link href="/admin">{t("Administration", "مدیریت")}</Link>
      {["SUPERADMIN", "AUDITOR"].includes(user.role) && <Link href="/admin/users">{t("Users", "کاربران")}</Link>}
      <span dir="ltr">{user.phone} · {user.role}</span>
      <button className={buttonClass} onClick={async () => { try { await api("auth/logout", "POST"); router.push("/login"); router.refresh(); } catch { setError(t("Sign-out failed. Please retry.", "خروج ناموفق بود. دوباره تلاش کنید.")); } }}>{t("Sign out", "خروج")}</button>
    </nav></aside>
    <section className="min-w-0">{error && <p role="alert">{error}</p>}{children}</section>
  </div>;
}

export function StaffWelcome() {
  const { t } = useIdentityLanguage();
  return <p>{t("Your account is signed in. No tools are available for this role yet.", "وارد حساب شدید. هنوز ابزاری برای این نقش ارائه نشده است.")}</p>;
}
