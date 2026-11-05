import Users from "@/components/identity/users";
import { staffUser } from "@/lib/identity/server";
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const user = await staffUser();
  if (!["SUPERADMIN", "AUDITOR"].includes(user.role)) return <p role="alert">Access denied / دسترسی ندارید</p>;
  const { id } = await params;
  return <Users key={id} actor={user} identifier={id} />;
}
