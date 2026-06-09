import { ProtectedShell } from "@/components/ProtectedShell";

export default function EmployeeLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedShell allowedRole="employee">{children}</ProtectedShell>;
}
