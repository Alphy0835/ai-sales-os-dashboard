import { API_URL } from "./api";
import { getAccessToken } from "./auth";

export type ReviewTask = {
  id: string;
  title: string;
  status: "pending" | "in_progress" | "done";
  created_at?: string;
  updated_at?: string;
  completed_at?: string | null;
};

export type ReviewRecord = {
  id: string;
  employee_id: string;
  employee_name: string;
  workspace_id: string;
  workspace_name: string;
  author_name: string;
  client_name: string | null;
  comment: string;
  discussion: string;
  created_at: string;
  tasks: ReviewTask[];
  tasks_done: number;
  tasks_total: number;
};

export type EmployeeTask = {
  id: string;
  title: string;
  status: ReviewTask["status"];
  review_id: string;
  review_date: string;
  author_name: string;
  workspace_name: string;
  updated_at: string;
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
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchManagerReviews(params?: {
  workspace_id?: string;
  employee_id?: string;
}): Promise<{ count: number; results: ReviewRecord[] }> {
  const qs = new URLSearchParams();
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id);
  if (params?.employee_id) qs.set("employee_id", params.employee_id);
  const q = qs.toString();
  return authFetch(`/api/v1/manager/reviews/${q ? `?${q}` : ""}`);
}

export function createReview(payload: {
  employee_id: string;
  workspace_id: string;
  comment: string;
  discussion?: string;
  client_id?: string;
  tasks: string[];
}): Promise<ReviewRecord> {
  return authFetch("/api/v1/manager/reviews/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateEmployeeTask(
  taskId: string,
  status: ReviewTask["status"],
): Promise<EmployeeTask> {
  return authFetch(`/api/v1/employee/tasks/${taskId}/`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
