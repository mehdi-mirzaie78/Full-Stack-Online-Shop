"use client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { phoneSchema, codeSchema, passwordSchema } from "@/lib/identity/validation";
import { api, parseUser } from "@/lib/identity/api";
import { buttonClass, fieldClass, useIdentityLanguage } from "./language";

export default function Login() {
  const { t } = useIdentityLanguage();
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [method, setMethod] = useState<"otp" | "password">("otp");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [expires, setExpires] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const [checking, setChecking] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const timer = setInterval(() => setRemaining(Math.max(0, Math.ceil((expires - Date.now()) / 1000))), 1000);
    return () => clearInterval(timer);
  }, [expires]);
  async function continueSession() {
    const user = parseUser(await api("auth/me"));
    router.replace(user.role === "CUSTOMER" ? "/" : "/admin"); router.refresh();
  }
  useEffect(() => {
    let active = true;
    void api("auth/me").then(value => {
      const user = parseUser(value);
      if (active) { router.replace(user.role === "CUSTOMER" ? "/" : "/admin"); router.refresh(); }
    }).catch(() => {}).finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, [router]);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const validation = phoneSchema.safeParse(phone);
      if (!validation.success) { setError(validation.error.issues[0].message); return; }
      if (method === "password") {
        const result = passwordSchema.safeParse(password);
        if (!result.success) { setError(result.error.issues[0].message); return; }
        await api("auth/password", "POST", { phone, password });
        await continueSession();
      } else if (!expires) {
        await api("auth/otp/request", "POST", { phone });
        setExpires(Date.now() + 120000); setRemaining(120);
      } else {
        const result = codeSchema.safeParse(code);
        if (!result.success) { setError(result.error.issues[0].message); return; }
        await api("auth/otp/verify", "POST", { phone, code });
        await continueSession();
      }
    } catch (failure) { setError(failure instanceof Error ? failure.message : t("Sign-in failed.", "ورود ناموفق بود.")); }
    finally { setBusy(false); }
  }
  return <div className="identity-login mx-auto max-w-xl space-y-6 p-8 sm:p-12">
    <h1 className="text-2xl font-bold">{t("Sign in", "ورود")}</h1>
    <p className="text-muted-foreground">{t("Enter your phone number to receive a sign-in code.", "برای دریافت کد ورود، شماره تلفن خود را وارد کنید.")}</p>
    <div className="flex gap-3" role="group" aria-label={t("Sign-in method", "روش ورود")}>
      <Button type="button" disabled={checking || busy} className={`${buttonClass} flex-1 aria-pressed:bg-cyan-300 aria-pressed:text-slate-950`} aria-pressed={method === "otp"} onClick={() => { setMethod("otp"); setExpires(0); setError(""); }}>{t("One-time code", "کد یک‌بارمصرف")}</Button>
      <Button type="button" disabled={checking || busy} className={`${buttonClass} flex-1 aria-pressed:bg-cyan-300 aria-pressed:text-slate-950`} aria-pressed={method === "password"} onClick={() => { setMethod("password"); setExpires(0); setError(""); }}>{t("Password", "رمز عبور")}</Button>
    </div>
    <form noValidate onSubmit={submit} className="space-y-4">
      <label className="block">{t("Phone number", "شماره تلفن")}
        <Input className={`${fieldClass} h-12`} type="tel" dir="ltr" maxLength={16} minLength={9} autoComplete="tel" placeholder="+989121234567" required pattern="\+[1-9][0-9]{7,14}" value={phone} disabled={Boolean(expires)} onChange={event => { const value = event.target.value; setPhone(value); const result = phoneSchema.safeParse(value); setError(result.success || !value ? "" : result.error.issues[0].message); }} />
      </label>
      {method === "password" && <label className="block">{t("Password", "رمز عبور")}<Input className={`${fieldClass} h-12`} type="password" autoComplete="current-password" maxLength={128} value={password} onChange={event => setPassword(event.target.value)} /></label>}
      {Boolean(expires) && <><label className="block">{t("Verification code", "کد تأیید")}
        <Input className={`${fieldClass} h-12`} dir="ltr" inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6} value={code} onChange={event => setCode(event.target.value)} />
      </label><p role="status">{t("Seconds remaining", "ثانیه باقی‌مانده")}: {remaining}</p></>}
      <Button type="submit" className={buttonClass} disabled={checking || busy || Boolean(expires && remaining === 0)}>{busy ? t("Please wait…", "لطفاً صبر کنید…") : method === "password" ? t("Sign in", "ورود") : expires ? t("Verify code", "تأیید کد") : t("Send code", "ارسال کد")}</Button>
    </form>
    {Boolean(expires) && <Button className={buttonClass} disabled={busy} onClick={() => { setExpires(0); setCode(""); }}>{t("Start again", "شروع دوباره")}</Button>}

    {error && <p role="alert">{error}</p>}
  </div>;
}
