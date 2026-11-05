import { redirect } from "next/navigation";
import { StaffWelcome } from "@/components/identity/staff-shell";
import { staffUser } from "@/lib/identity/server";
export default async function Page() {
  const user = await staffUser();
  if (["SUPERADMIN", "AUDITOR"].includes(user.role)) redirect("/admin/users");
  return <StaffWelcome />;
}
