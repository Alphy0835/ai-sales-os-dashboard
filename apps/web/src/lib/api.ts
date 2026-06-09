import { clearSession, getAccessToken, getRefreshToken, setAccessToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let refreshInFlight: Promise<string> | null = null;

function redirectToLogin() {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

export async function refreshAccessToken(): Promise<string> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refresh = getRefreshToken();
    if (!refresh) throw new Error("No refresh token");

    const res = await fetch(`${API_URL}/api/v1/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });

    if (!res.ok) throw new Error("Refresh failed");

    const data = (await res.json()) as { access: string };
    setAccessToken(data.access);
    return data.access;
  })().finally(() => {
    refreshInFlight = null;
  });

  return refreshInFlight;
}

export async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const makeRequest = (accessToken: string) =>
    fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });

  let token = getAccessToken();
  if (!token) throw new Error("Not authenticated");

  let res = await makeRequest(token);

  if (res.status === 401) {
    try {
      token = await refreshAccessToken();
    } catch {
      clearSession();
      redirectToLogin();
      throw new Error("Session expired");
    }
    res = await makeRequest(token);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error_message ?? body.detail ?? body.message ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type UserRole = "manager" | "employee";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  tenant_id: string;
  workspace_id?: string | null;
  workspace_name?: string | null;
};

export type MeResponse = AuthUser & {
  workspace: { id: string; name: string } | null;
  permissions: Record<string, string>;
};

export type LoginResponse = {
  access: string;
  refresh: string;
  user: AuthUser;
};

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? body.message ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/api/v1/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJson<LoginResponse>(res);
}

export async function fetchMe(): Promise<MeResponse> {
  return authFetch<MeResponse>("/api/v1/auth/me/");
}

export { API_URL };
