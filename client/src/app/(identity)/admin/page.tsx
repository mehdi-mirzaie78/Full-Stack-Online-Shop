import { canManageIdentity } from "@/lib/identity/api";
import { redirect } from "next/navigation";
import { StaffWelcome } from "@/components/identity/staff-shell";
import { staffUser } from "@/lib/identity/server";
export default async function Page() {
  const user = await staffUser();
  if (canManageIdentity(user)) redirect("/admin/users");
  return <StaffWelcome />;
}
