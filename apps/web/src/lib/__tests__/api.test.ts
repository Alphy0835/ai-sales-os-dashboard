import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clearSession } from "../auth";

vi.mock("../auth", () => ({
  clearSession: vi.fn(),
}));

describe("api", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
    vi.mocked(clearSession).mockClear();
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function jsonResponse(data: unknown, status = 200) {
    return {
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(data),
    } as Response;
  }

  it("login posts credentials with cookies", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ user: sampleUser }));
    const { login } = await import("../api");
    const result = await login("manager@demo.local", "demo1234");
    expect(result.user.email).toBe("manager@demo.local");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/login/",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email: "manager@demo.local", password: "demo1234" }),
      }),
    );
  });

  it("login throws on error response", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Неверные учётные данные" }, 401));
    const { login } = await import("../api");
    await expect(login("bad@demo.local", "wrong")).rejects.toThrow("Неверные учётные данные");
  });

  it("logout calls logout endpoint", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({}));
    const { logout } = await import("../api");
    await logout();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout/",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });

  it("fetchMe uses authFetch path", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(mePayload));
    const { fetchMe } = await import("../api");
    const me = await fetchMe();
    expect(me.permissions.reviews).toBe("edit");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/me/",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("authFetch refreshes on 401 and retries", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({}, 401))
      .mockResolvedValueOnce(jsonResponse({}))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));
    const { authFetch } = await import("../api");
    const data = await authFetch<{ ok: boolean }>("/api/v1/test/");
    expect(data.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/auth/refresh/");
  });

  it("authFetch clears session when refresh fails", async () => {
    const location = { href: "" };
    vi.stubGlobal("location", location);
    fetchMock.mockResolvedValueOnce(jsonResponse({}, 401)).mockResolvedValueOnce(jsonResponse({}, 401));
    const { authFetch } = await import("../api");
    await expect(authFetch("/api/v1/protected/")).rejects.toThrow("Session expired");
    expect(clearSession).toHaveBeenCalled();
    expect(location.href).toBe("/login");
  });

  it("refreshAccessToken posts to refresh endpoint", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({}));
    const { refreshAccessToken } = await import("../api");
    await refreshAccessToken();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/refresh/",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });
});

const sampleUser = {
  id: "u1",
  email: "manager@demo.local",
  full_name: "Demo Manager",
  role: "manager" as const,
  tenant_id: "t1",
};

const mePayload = {
  ...sampleUser,
  workspace: { id: "ws1", name: "ОП Москва" },
  permissions: { reviews: "edit", analytics: "run" },
};
