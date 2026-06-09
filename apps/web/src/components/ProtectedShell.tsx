"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { fetchMe, logout as logoutApi } from "@/lib/api";
import type { AuthUser } from "@/lib/api";
import {
  clearSession,
  getStoredUser,
  homeRouteForRole,
  saveMeUser,
} from "@/lib/auth";
import { AmbientBackground, AppShell } from "@/components/AppShell";

type Props = {
  allowedRole: AuthUser["role"];
  children: ReactNode;
};

export function ProtectedShell({ allowedRole, children }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored && stored.role !== allowedRole) {
      router.replace(homeRouteForRole(stored.role));
      return;
    }

    fetchMe()
      .then((me) => {
        if (me.role !== allowedRole) {
          router.replace(homeRouteForRole(me.role));
          return;
        }
        saveMeUser(me);
        setUser({
          id: me.id,
          email: me.email,
          full_name: me.full_name,
          role: me.role,
          tenant_id: me.tenant_id,
          workspace_id: me.workspace?.id ?? null,
          workspace_name: me.workspace?.name ?? null,
        });
        setReady(true);
      })
      .catch(() => {
        clearSession();
        router.replace("/login");
      });
  }, [allowedRole, router]);

  const logout = async () => {
    try {
      await logoutApi();
    } finally {
      clearSession();
      router.replace("/login");
    }
  };

  if (!ready || !user) {
    return (
      <>
        <AmbientBackground />
        <div className="relative z-[1] flex min-h-screen items-center justify-center text-secondary">
          Загрузка…
        </div>
      </>
    );
  }

  return (
    <>
      <AmbientBackground />
      <AppShell
        variant={allowedRole}
        workspaceName={user.workspace_name}
        onLogout={logout}
      >
        {children}
      </AppShell>
    </>
  );
}
