"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ApiError, fetchMe, logout as logoutApi } from "@/lib/api";
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

type ShellState = "loading" | "ready" | "forbidden";

export function ProtectedShell({ allowedRole, children }: Props) {
  const router = useRouter();
  const [state, setState] = useState<ShellState>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [permissions, setPermissions] = useState<Record<string, string>>({});
  const [forbiddenMessage, setForbiddenMessage] = useState<string | null>(null);

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
        setPermissions(me.permissions);
        setUser({
          id: me.id,
          email: me.email,
          full_name: me.full_name,
          role: me.role,
          tenant_id: me.tenant_id,
          workspace_id: me.workspace?.id ?? null,
          workspace_name: me.workspace?.name ?? null,
        });
        setState("ready");
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          setForbiddenMessage(err.message);
          setState("forbidden");
          return;
        }
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

  if (state === "forbidden") {
    return (
      <>
        <AmbientBackground />
        <div className="relative z-[1] flex min-h-screen items-center justify-center p-4">
          <div className="card card-pad max-w-md text-center">
            <h1 className="page-title mb-2">Доступ запрещён</h1>
            <p className="text-secondary mb-4">
              {forbiddenMessage ?? "Учётная запись неактивна или доступ ограничен."}
            </p>
            <button type="button" className="btn-secondary" onClick={logout}>
              Выйти
            </button>
          </div>
        </div>
      </>
    );
  }

  if (state !== "ready" || !user) {
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
        permissions={permissions}
        onLogout={logout}
      >
        {children}
      </AppShell>
    </>
  );
}
