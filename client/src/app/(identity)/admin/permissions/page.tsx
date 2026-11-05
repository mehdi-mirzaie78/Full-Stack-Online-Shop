import PermissionSettings from "@/components/identity/permission-settings";
import { staffUser } from "@/lib/identity/server";
export default async function Page() {
  const actor = await staffUser();
  if (actor.role !== "SUPERADMIN") return <p role="alert">Access denied / دسترسی ندارید</p>;
  return <PermissionSettings />;
}
