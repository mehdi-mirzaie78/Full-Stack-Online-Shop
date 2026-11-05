import { canManageIdentity } from "@/lib/identity/api";
import Users from "@/components/identity/users";
import { staffUser } from "@/lib/identity/server";
export default async function Page() {
  const user = await staffUser();
  if (!canManageIdentity(user)) return <p role="alert">Access denied / دسترسی ندارید</p>;
  return <Users actor={user} />;
}
