import { clearSession } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

let refreshInFlight: Promise<void> | null = null;

function redirectToLogin() {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

export async function refreshAccessToken(): Promise<void> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh/`, {
      method: "POST",
      credentials: "include",
    });

    if (!res.ok) throw new Error("Refresh failed");
  })().finally(() => {
    refreshInFlight = null;
  });

  return refreshInFlight;
}

export async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const makeRequest = () =>
    fetch(`${API_URL}${path}`, {
      credentials: "include",
      ...init,
      headers: {
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });

  let res = await makeRequest();

  if (res.status === 401) {
    try {
      await refreshAccessToken();
    } catch {
      clearSession();
      redirectToLogin();
      throw new Error("Session expired");
    }
    res = await makeRequest();
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
  user: AuthUser;
  access?: string;
  refresh?: string;
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
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJson<LoginResponse>(res);
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/api/v1/auth/logout/`, {
    method: "POST",
    credentials: "include",
  });
}

export async function fetchMe(): Promise<MeResponse> {
  return authFetch<MeResponse>("/api/v1/auth/me/");
}

export { API_URL };
