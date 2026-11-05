"use client";
import { usePathname } from "next/navigation";
import { Navbar } from "./navbar";
export function SiteFrame({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  if (path === "/admin" || path.startsWith("/admin/")) return children;
  return <><Navbar /><main className="container mx-auto px-4 py-8">{children}</main></>;
}
