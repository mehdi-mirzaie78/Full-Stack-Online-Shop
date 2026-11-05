import StaffShell from "@/components/identity/staff-shell";
import { staffUser } from "@/lib/identity/server";
export default async function Layout({ children }: { children: React.ReactNode }) {
  return <StaffShell user={await staffUser()}>{children}</StaffShell>;
}
