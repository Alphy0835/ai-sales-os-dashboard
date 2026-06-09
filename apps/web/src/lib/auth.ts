import type { AuthUser, MeResponse } from "./api";

const ACCESS_KEY = "ai_sales_os_access";
const REFRESH_KEY = "ai_sales_os_refresh";
const USER_KEY = "ai_sales_os_user";

export function saveSession(access: string, refresh: string, user: AuthUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setAccessToken(access: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, access);
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
  saveSession(getAccessToken() ?? "", getRefreshToken() ?? "", {
    id: me.id,
    email: me.email,
    full_name: me.full_name,
    role: me.role,
    tenant_id: me.tenant_id,
    workspace_id: me.workspace?.id ?? null,
    workspace_name: me.workspace?.name ?? null,
  });
}
