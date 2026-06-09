const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function fetchMe(accessToken: string): Promise<MeResponse> {
  const res = await fetch(`${API_URL}/api/v1/auth/me/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return parseJson<MeResponse>(res);
}

export { API_URL };
