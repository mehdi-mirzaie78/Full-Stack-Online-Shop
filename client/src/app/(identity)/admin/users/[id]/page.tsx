import { canManageIdentity } from "@/lib/identity/api";
import Users from "@/components/identity/users";
import { staffUser } from "@/lib/identity/server";
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const user = await staffUser();
  if (!canManageIdentity(user)) return <p role="alert">Access denied / دسترسی ندارید</p>;
  const { id } = await params;
  return <Users key={id} actor={user} identifier={id} />;
}
