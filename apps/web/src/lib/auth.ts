import type { AuthUser, MeResponse } from "./api";

const USER_KEY = "ai_sales_os_user";
const PERMISSIONS_KEY = "ai_sales_os_permissions";

export function saveSession(user: AuthUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(PERMISSIONS_KEY);
}

export function getStoredPermissions(): Record<string, string> | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(PERMISSIONS_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Record<string, string>;
  } catch {
    return null;
  }
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function homeRouteForRole(role: AuthUser["role"]): string {
  return role === "manager" ? "/manager" : "/employee";
}

export function saveMeUser(me: MeResponse) {
  saveSession({
    id: me.id,
    email: me.email,
    full_name: me.full_name,
    role: me.role,
    tenant_id: me.tenant_id,
    workspace_id: me.workspace?.id ?? null,
    workspace_name: me.workspace?.name ?? null,
  });
  if (typeof window !== "undefined") {
    localStorage.setItem(PERMISSIONS_KEY, JSON.stringify(me.permissions));
  }
}
