import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  clearSession,
  getStoredUser,
  homeRouteForRole,
  saveMeUser,
  saveSession,
} from "../auth";
import type { AuthUser } from "../api";

const sampleUser: AuthUser = {
  id: "u1",
  email: "manager@demo.local",
  full_name: "Demo Manager",
  role: "manager",
  tenant_id: "t1",
};

describe("auth", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("saveSession and getStoredUser round-trip", () => {
    saveSession(sampleUser);
    expect(getStoredUser()).toEqual(sampleUser);
  });

  it("clearSession removes stored user", () => {
    saveSession(sampleUser);
    clearSession();
    expect(getStoredUser()).toBeNull();
  });

  it("getStoredUser returns null for invalid JSON", () => {
    localStorage.setItem("ai_sales_os_user", "{not-json");
    expect(getStoredUser()).toBeNull();
  });

  it("homeRouteForRole maps roles to home paths", () => {
    expect(homeRouteForRole("manager")).toBe("/manager");
    expect(homeRouteForRole("employee")).toBe("/employee");
  });

  it("saveMeUser maps workspace into AuthUser", () => {
    saveMeUser({
      ...sampleUser,
      workspace: { id: "ws1", name: "ОП Москва" },
      permissions: { reviews: "edit" },
    });
    expect(getStoredUser()).toMatchObject({
      workspace_id: "ws1",
      workspace_name: "ОП Москва",
    });
  });
});
