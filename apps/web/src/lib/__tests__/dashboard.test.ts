import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("dashboard query builders", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function jsonResponse(data: unknown) {
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    } as Response;
  }

  it("fetchManagerDashboard calls base path without params", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ filters: {} }));
    const { fetchManagerDashboard } = await import("../dashboard");
    await fetchManagerDashboard();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/manager/dashboard",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("fetchManagerDashboard appends workspace_id and user_id", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ filters: {} }));
    const { fetchManagerDashboard } = await import("../dashboard");
    await fetchManagerDashboard({ workspace_id: "ws-1", user_id: "u-2" });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/manager/dashboard?");
    expect(url).toContain("workspace_id=ws-1");
    expect(url).toContain("user_id=u-2");
  });

  it("fetchManagerClients builds filter query string", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ count: 0, results: [] }));
    const { fetchManagerClients } = await import("../dashboard");
    await fetchManagerClients({
      workspace_id: "ws-1",
      employee_id: "emp-1",
      status: "new",
    });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/manager/clients?");
    expect(url).toContain("workspace_id=ws-1");
    expect(url).toContain("employee_id=emp-1");
    expect(url).toContain("status=new");
  });

  it("fetchEmployeeDashboard calls employee endpoint", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ filters: {}, periods: {}, employees: [] }));
    const { fetchEmployeeDashboard } = await import("../dashboard");
    await fetchEmployeeDashboard();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/employee/dashboard/",
      expect.objectContaining({ credentials: "include" }),
    );
  });
});
