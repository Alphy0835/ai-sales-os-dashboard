import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("reviews query builders", () => {
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

  it("fetchManagerReviews calls list endpoint without params", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ count: 0, results: [] }));
    const { fetchManagerReviews } = await import("../reviews");
    await fetchManagerReviews();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/manager/reviews/",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("fetchManagerReviews appends workspace_id and employee_id", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ count: 0, results: [] }));
    const { fetchManagerReviews } = await import("../reviews");
    await fetchManagerReviews({ workspace_id: "ws-1", employee_id: "emp-1" });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/manager/reviews/?");
    expect(url).toContain("workspace_id=ws-1");
    expect(url).toContain("employee_id=emp-1");
  });

  it("createReview posts JSON payload", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ id: "r1" }));
    const { createReview } = await import("../reviews");
    await createReview({
      employee_id: "emp-1",
      workspace_id: "ws-1",
      comment: "Good job",
      tasks: ["Task 1"],
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/manager/reviews/",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          employee_id: "emp-1",
          workspace_id: "ws-1",
          comment: "Good job",
          tasks: ["Task 1"],
        }),
      }),
    );
  });

  it("updateEmployeeTask patches task status", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ id: "t1", status: "done" }));
    const { updateEmployeeTask } = await import("../reviews");
    await updateEmployeeTask("t1", "done");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/employee/tasks/t1/",
      expect.objectContaining({
        method: "PATCH",
        credentials: "include",
        body: JSON.stringify({ status: "done" }),
      }),
    );
  });
});
