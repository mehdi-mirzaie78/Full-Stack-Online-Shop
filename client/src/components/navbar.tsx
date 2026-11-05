"use client";
import Link from "next/link";
import { DirectionProvider } from "@base-ui/react/direction-provider";
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList } from "@/components/ui/navigation-menu";
import { LanguageToggle, useIdentityLanguage } from "@/components/identity/language";

export function Navbar() {
  const { persian, t } = useIdentityLanguage();
  return <header dir="ltr" className="sticky top-0 z-50 border-b border-border/60 bg-background/95 px-4 py-3 backdrop-blur-md sm:px-6">
    <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)_auto] items-center gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto]">
      <Link href="/" lang="en" className="text-lg font-extrabold text-neon-cyan sm:text-xl">CYBER//STORE</Link>
      <DirectionProvider direction={persian ? "rtl" : "ltr"}>
        <div dir={persian ? "rtl" : "ltr"} className="col-span-2 row-start-2 justify-self-center sm:col-span-1 sm:col-start-2 sm:row-start-1">
          <NavigationMenu aria-label={t("Main navigation", "ناوبری اصلی")}>
            <NavigationMenuList>
              {[["/", t("Storefront", "فروشگاه")], ["/login", t("Sign in", "ورود")], ["/admin", t("Administration", "مدیریت")]].map(([href, label]) => <NavigationMenuItem key={href}>
                <NavigationMenuLink render={<Link href={href} />} className="rounded-lg px-3 py-2 text-sm hover:bg-secondary focus-visible:outline focus-visible:outline-2">{label}</NavigationMenuLink>
              </NavigationMenuItem>)}
            </NavigationMenuList>
          </NavigationMenu>
        </div>
      </DirectionProvider>
      <div className="col-start-2 row-start-1 justify-self-end sm:col-start-3"><LanguageToggle /></div>
    </div>
  </header>;
}
