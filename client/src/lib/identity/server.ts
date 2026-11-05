import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiBase, parseUser, type User } from "./api";

export async function staffUser(): Promise<User> {
  const store = await cookies();
  const access = store.get("shop_access");
  if (!access) redirect("/login");
  const response = await fetch(`${apiBase}/auth/me`, {
    headers: { Cookie: `shop_access=${encodeURIComponent(access.value)}` }, cache: "no-store",
  });
  if (response.status === 401 || response.status === 403) redirect("/login");
  if (!response.ok) throw new Error("Identity service is unavailable.");
  const user = parseUser(await response.json());
  if (user.role === "CUSTOMER" || !user.is_active || user.is_deleted) redirect("/login?staff=required");
  return user;
}
