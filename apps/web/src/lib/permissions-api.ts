import { authFetch } from "./api";

export type PermissionUser = {
  id: string;
  email: string;
  full_name: string;
  role: "manager" | "employee";
  workspace: { id: string; name: string } | null;
  permissions: Record<string, string>;
};

export type AuditLogEntry = {
  id: string;
  action: string;
  module: string;
  old_level: string;
  new_level: string;
  actor: { id: string; email: string; full_name: string };
  target_user: { id: string; email: string; full_name: string };
  created_at: string;
};

export type KnowledgeGrant = {
  article_id: string;
  title: string;
  access_level: string;
  base_accessible: boolean;
  is_allowed: boolean | null;
  grantor_can_assign: boolean;
};

export type ScopeResponse = {
  workspaces: { id: string; name: string }[];
  users: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    workspace: { id: string; name: string } | null;
  }[];
};

const MODULES = ["dashboard", "clients", "reviews", "analytics", "settings", "agent"] as const;
export const PERMISSION_MODULES = MODULES;

export const MODULE_LABELS: Record<string, string> = {
  dashboard: "Дашборд",
  clients: "Клиенты",
  reviews: "Разборы",
  analytics: "Аналитика",
  settings: "Настройки",
  agent: "AI-агент",
};

export const LEVEL_OPTIONS = ["none", "view", "edit", "run", "use"] as const;

export async function fetchScopeUsers(): Promise<ScopeResponse> {
  return authFetch<ScopeResponse>("/api/v1/scope/");
}

export async function fetchPermissionUsers(): Promise<{ results: PermissionUser[] }> {
  return authFetch<{ results: PermissionUser[] }>("/api/v1/permissions/users/");
}

export async function fetchUserPermissions(userId: string): Promise<PermissionUser> {
  return authFetch<PermissionUser>(`/api/v1/permissions/users/${userId}/`);
}

export async function updateUserPermissions(
  userId: string,
  permissions: Record<string, string>
): Promise<PermissionUser> {
  return authFetch<PermissionUser>(`/api/v1/permissions/users/${userId}/`, {
    method: "PUT",
    body: JSON.stringify({ permissions }),
  });
}

export async function fetchPermissionAudit(userId?: string): Promise<{ results: AuditLogEntry[] }> {
  const q = userId ? `?user_id=${userId}&limit=30` : "?limit=30";
  return authFetch<{ results: AuditLogEntry[] }>(`/api/v1/audit/permissions/${q}`);
}

export async function fetchKnowledgeGrants(userId: string): Promise<{ grants: KnowledgeGrant[] }> {
  return authFetch<{ grants: KnowledgeGrant[] }>(`/api/v1/permissions/users/${userId}/knowledge/`);
}

export async function updateKnowledgeGrants(
  userId: string,
  grants: { article_id: string; is_allowed: boolean | null }[]
): Promise<{ grants: KnowledgeGrant[] }> {
  return authFetch<{ grants: KnowledgeGrant[] }>(`/api/v1/permissions/users/${userId}/knowledge/`, {
    method: "PUT",
    body: JSON.stringify({ grants }),
  });
}
