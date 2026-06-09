import { API_URL } from "./api";
import { getAccessToken } from "./auth";

export type QualityCriterion = {
  id: string;
  name: string;
  description: string;
  funnel_stage: string;
  stage_label: string;
  keywords: string;
  is_active: boolean;
  sort_order: number;
};

export type AnalyticsReport = {
  id: string;
  template: string;
  template_label: string;
  custom_report_title: string | null;
  status: string;
  workspace_id: string;
  workspace_name: string;
  employee_id: string | null;
  employee_name: string | null;
  author_name: string;
  summary_text: string;
  canvas: {
    overall_score: number | null;
    stages: Array<{ stage: string; label: string; score: number | null; criteria_count: number }>;
    criteria: Array<{
      name: string;
      score: number | null;
      stage_label: string;
      matched_keywords: string[];
    }>;
    recommendations: Array<{ type: string; text: string; criterion_id?: string }>;
    highlights: Array<{ type: string; text: string }>;
  };
  error_message: string;
  recordings_analyzed: number;
  created_at: string;
};

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error_message ?? body.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function fetchQualityCriteria(): Promise<{ count: number; results: QualityCriterion[] }> {
  return authFetch("/api/v1/manager/settings/quality-criteria/");
}

export function createQualityCriterion(payload: Partial<QualityCriterion>): Promise<QualityCriterion> {
  return authFetch("/api/v1/manager/settings/quality-criteria/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateQualityCriterion(id: string, payload: Partial<QualityCriterion>): Promise<QualityCriterion> {
  return authFetch(`/api/v1/manager/settings/quality-criteria/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteQualityCriterion(id: string): Promise<void> {
  return authFetch(`/api/v1/manager/settings/quality-criteria/${id}/`, { method: "DELETE" });
}

export function fetchAnalyticsReports(): Promise<{ count: number; results: AnalyticsReport[] }> {
  return authFetch("/api/v1/manager/analytics/reports/");
}

export function runAnalyticsReport(payload: {
  workspace_id: string;
  employee_id?: string;
  template?: string;
  custom_report_id?: string;
}): Promise<AnalyticsReport> {
  return authFetch("/api/v1/manager/analytics/reports/run/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type CustomReport = {
  id: string;
  title: string;
  description: string;
  structured_query: {
    focus_stages?: string[];
    focus_keywords?: string[];
    engine?: string;
  };
  is_active: boolean;
  author_name: string;
  created_at: string;
  updated_at: string;
};

export function fetchCustomReports(): Promise<{ count: number; results: CustomReport[] }> {
  return authFetch("/api/v1/manager/settings/custom-reports/");
}

export function createCustomReport(payload: { title: string; description: string }): Promise<CustomReport> {
  return authFetch("/api/v1/manager/settings/custom-reports/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteCustomReport(id: string): Promise<void> {
  return authFetch(`/api/v1/manager/settings/custom-reports/${id}/`, { method: "DELETE" });
}
