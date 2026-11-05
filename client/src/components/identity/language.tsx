"use client";
import { Button } from "@/components/ui/button";
import { createContext, useContext, useEffect, useState } from "react";

const Language = createContext({ toggle: () => {}, persian: true, t: (english: string, persian: string) => english || persian });
export function IdentityLanguage({ children }: { children: React.ReactNode }) {
  const [persian, setPersian] = useState(true);
  useEffect(() => {
    document.documentElement.lang = persian ? "fa" : "en";
    document.documentElement.dir = persian ? "rtl" : "ltr";
  }, [persian]);
  return <Language.Provider value={{ persian, toggle: () => setPersian(value => !value), t: (en, fa) => persian ? fa : en }}>
    {children}
  </Language.Provider>;
}
export const useIdentityLanguage = () => useContext(Language);
export const fieldClass = "h-12 w-full rounded-xl border border-slate-600/60 bg-slate-950/60 px-4 py-3 text-base outline-none focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/20";
export const buttonClass = "min-h-11 rounded-xl border border-cyan-300/50 bg-cyan-300/10 px-5 py-2.5 font-medium text-cyan-100 transition-colors hover:bg-cyan-300/20 disabled:opacity-50 focus-visible:outline focus-visible:outline-2";

export function LanguageToggle() {
  const { persian, toggle } = useContext(Language);
  return <Button type="button" onClick={toggle} className={`${buttonClass} w-28 min-h-11 shrink-0`}>{persian ? "English" : "فارسی"}</Button>;
}
