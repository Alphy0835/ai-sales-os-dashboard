"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = { href: string; label: string; icon: string; module?: string };

const managerNav: NavItem[] = [
  { href: "/manager", label: "Дашборд", icon: "▦", module: "dashboard" },
  { href: "/manager/clients", label: "Клиенты к разбору", icon: "◎", module: "clients" },
  { href: "/manager/reviews", label: "История разборов", icon: "☰", module: "reviews" },
  { href: "/manager/analytics", label: "AI-аналитика", icon: "↗", module: "analytics" },
  { href: "/manager/agent", label: "AI-агент", icon: "✦", module: "agent" },
  { href: "/manager/settings", label: "Настройки", icon: "⚙", module: "settings" },
];

const employeeNav: NavItem[] = [
  { href: "/employee", label: "Дашборд", icon: "▦", module: "dashboard" },
  { href: "/employee/agent", label: "AI-агент", icon: "✦", module: "agent" },
];

type ShellProps = {
  variant: "manager" | "employee";
  workspaceName?: string | null;
  permissions?: Record<string, string>;
  onLogout: () => void;
  children: ReactNode;
};

function isNavActive(pathname: string, href: string) {
  if (href === "/manager" || href === "/employee") return pathname === href;
  return pathname.startsWith(href);
}

function filterNavByPermissions(nav: NavItem[], permissions?: Record<string, string>) {
  if (!permissions) return nav;
  return nav.filter((item) => !item.module || permissions[item.module] !== "none");
}

export function AppShell({ variant, workspaceName, permissions, onLogout, children }: ShellProps) {
  const pathname = usePathname();
  const nav = filterNavByPermissions(variant === "manager" ? managerNav : employeeNav, permissions);

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
            className={`nav-item${isNavActive(pathname, item.href) ? " active" : ""}`}
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
      <main className="flex min-w-0 flex-1">{children}</main>
    </div>
  );
}

export function AmbientBackground() {
  return <div className="ambient" aria-hidden />;
}
