import { authFetch } from "./api";

export type MetricPeriod = "today" | "week" | "month";

export type MetricsSummary = {
  period: string;
  completeness: string;
  completeness_reason: string | null;
  sources: Array<{
    id?: string;
    source_type: string;
    status: string;
    name: string;
    last_error: string | null;
  }>;
  metrics: Record<
    string,
    {
      label: string;
      value: number | null;
      available: boolean;
      reason: string | null;
    }
  >;
};

export type ManagerDashboard = {
  filters: {
    workspaces: Array<{ id: string; name: string }>;
    employees: Array<{ id: string; full_name: string }>;
    workspace_id: string | null;
    user_id: string | null;
  };
  periods: Record<MetricPeriod, MetricsSummary>;
  hero: {
    calls: number | null;
    quality_score: number | null;
    quality_available: boolean;
    plan_calls: number;
    plan_quality: number;
  };
  employees: Array<{
    id: string;
    full_name: string;
    calls: number;
    quality_score: number | null;
    status: string;
    status_label: string;
  }>;
  ai_summary: {
    available: boolean;
    text: string;
    confidence: number;
    sources: string[];
    highlights: Array<{ type: string; text: string }>;
  } | null;
  trend: { labels: string[]; values: number[] };
  attention: { count: number; text: string | null };
};

export type ClientToReview = {
  id: string;
  client_name: string;
  reason: string;
  priority: string;
  status: string;
  employee_id: string;
  employee_name: string;
  workspace_id: string;
  workspace_name: string;
};

export function fetchManagerDashboard(params?: {
  workspace_id?: string;
  user_id?: string;
}): Promise<ManagerDashboard> {
  const qs = new URLSearchParams();
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id);
  if (params?.user_id) qs.set("user_id", params.user_id);
  const q = qs.toString();
  return authFetch(`/api/v1/manager/dashboard${q ? `?${q}` : ""}`);
}

export function fetchManagerClients(params?: {
  workspace_id?: string;
  employee_id?: string;
  status?: string;
}): Promise<{ count: number; results: ClientToReview[] }> {
  const qs = new URLSearchParams();
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id);
  if (params?.employee_id) qs.set("employee_id", params.employee_id);
  if (params?.status) qs.set("status", params.status);
  const q = qs.toString();
  return authFetch(`/api/v1/manager/clients${q ? `?${q}` : ""}`);
}

export function fetchEmployeeDashboard(): Promise<{
  periods: Record<MetricPeriod, MetricsSummary>;
  hero: { full_name: string };
  tasks: Array<{
    id: string;
    title: string;
    status: "pending" | "in_progress" | "done";
    review_id: string;
    review_date: string;
    author_name: string;
    workspace_name: string;
    updated_at: string;
  }>;
}> {
  return authFetch("/api/v1/employee/dashboard/");
}
