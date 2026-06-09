"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = { href: string; label: string; icon: string };

const managerNav: NavItem[] = [
  { href: "/manager", label: "Дашборд", icon: "▦" },
  { href: "/manager/clients", label: "Клиенты к разбору", icon: "◎" },
  { href: "/manager/reviews", label: "История разборов", icon: "☰" },
  { href: "/manager/analytics", label: "AI-аналитика", icon: "↗" },
  { href: "/manager/agent", label: "AI-агент", icon: "✦" },
  { href: "/manager/settings", label: "Настройки", icon: "⚙" },
];

const employeeNav: NavItem[] = [
  { href: "/employee", label: "Дашборд", icon: "▦" },
  { href: "/employee/agent", label: "AI-агент", icon: "✦" },
];

type ShellProps = {
  variant: "manager" | "employee";
  workspaceName?: string | null;
  onLogout: () => void;
  children: ReactNode;
};

export function AppShell({ variant, workspaceName, onLogout, children }: ShellProps) {
  const pathname = usePathname();
  const nav = variant === "manager" ? managerNav : employeeNav;

  return (
    <div className="relative z-[1] flex min-h-screen max-w-[1540px] mx-auto p-4 gap-[var(--gap-page)]">
      <aside
        className="flex w-[var(--sidebar-w)] shrink-0 flex-col gap-1 rounded-[var(--radius-shell)] p-[18px_14px]"
        style={{
          backgroundColor: "rgba(6, 8, 11, 0.47)",
          boxShadow: "0 24px 48px rgba(0,0,0,0.45)",
        }}
      >
        <div className="flex items-center gap-2.5 px-2.5 pb-3 text-sm font-bold">
          <div className="h-8 w-8 rounded-[11px] bg-accent-cyan/10" />
          AI Sales OS
        </div>
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item${pathname === item.href ? " active" : ""}`}
          >
            <span>{item.icon}</span> {item.label}
          </Link>
        ))}
        <div className="flex-1" />
        <div className="border-t border-white/5 pt-2 mt-1">
          {workspaceName && (
            <div className="px-3 pb-1 text-[10px] uppercase tracking-wide text-muted">{workspaceName}</div>
          )}
          <button type="button" className="nav-item w-full text-left" onClick={onLogout}>
            ⎋ Выход
          </button>
        </div>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col gap-[var(--gap-page)]">{children}</main>
    </div>
  );
}

export function AmbientBackground() {
  return <div className="ambient" aria-hidden />;
}
