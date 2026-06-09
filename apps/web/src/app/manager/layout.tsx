import { ProtectedShell } from "@/components/ProtectedShell";

export default function ManagerLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedShell allowedRole="manager">{children}</ProtectedShell>;
}
