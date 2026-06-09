"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fetchMe } from "@/lib/api";
import { fetchManagerDashboard } from "@/lib/dashboard";
import { createReview, fetchManagerReviews, type ReviewRecord } from "@/lib/reviews";

const STATUS_LABELS: Record<string, string> = {
  pending: "Ожидает",
  in_progress: "В работе",
  done: "Готово",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function ReviewHistoryView() {
  const searchParams = useSearchParams();
  const [workspaceId, setWorkspaceId] = useState(searchParams.get("workspace_id") ?? "");
  const [employeeId, setEmployeeId] = useState(searchParams.get("employee_id") ?? "");
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [workspaces, setWorkspaces] = useState<Array<{ id: string; name: string }>>([]);
  const [employees, setEmployees] = useState<Array<{ id: string; full_name: string }>>([]);
  const [canEdit, setCanEdit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(Boolean(searchParams.get("employee_id")));
  const [form, setForm] = useState({
    comment: "",
    discussion: "",
    tasks: "",
    client_id: searchParams.get("client_id") ?? "",
  });
  const [saving, setSaving] = useState(false);

  const prefillWorkspace = searchParams.get("workspace_id") ?? "";

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dash, list, me] = await Promise.all([
        fetchManagerDashboard({
          workspace_id: workspaceId || undefined,
          user_id: employeeId || undefined,
        }),
        fetchManagerReviews({
          workspace_id: workspaceId || undefined,
          employee_id: employeeId || undefined,
        }),
        fetchMe(),
      ]);
      setWorkspaces(dash.filters.workspaces);
      setEmployees(dash.filters.employees);
      setReviews(list.results);
      setCanEdit(me?.permissions.reviews === "edit");
      if (!workspaceId && prefillWorkspace) setWorkspaceId(prefillWorkspace);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [workspaceId, employeeId, prefillWorkspace]);

  useEffect(() => {
    load();
  }, [load]);

  const selectedEmployee = useMemo(
    () => employees.find((e) => e.id === employeeId),
    [employees, employeeId],
  );

  const submitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!employeeId || !workspaceId) {
      setError("Выберите подразделение и сотрудника");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createReview({
        employee_id: employeeId,
        workspace_id: workspaceId,
        comment: form.comment,
        discussion: form.discussion,
        client_id: form.client_id || undefined,
        tasks: form.tasks
          .split("\n")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      setForm({ comment: "", discussion: "", tasks: "", client_id: "" });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="manager-layout">
      <div className="manager-main">
        <header>
          <h1 className="page-title">История разборов</h1>
          <p className="page-subtitle">Записи разборов с сотрудниками и поставленные задачи</p>
        </header>

        <div className="card card-pad mb-4">
          <div className="filters-row flex flex-wrap gap-3 items-end">
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Подразделение
              <select
                className="input"
                value={workspaceId}
                onChange={(e) => setWorkspaceId(e.target.value)}
              >
                <option value="">Все</option>
                {workspaces.map((ws) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Сотрудник
              <select
                className="input"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
              >
                <option value="">Все</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.full_name}
                  </option>
                ))}
              </select>
            </label>
            {canEdit && (
              <button type="button" className="btn btn-primary ml-auto" onClick={() => setShowForm((v) => !v)}>
                {showForm ? "Скрыть форму" : "Новый разбор"}
              </button>
            )}
          </div>
        </div>

        {showForm && canEdit && (
          <form className="card card-pad mb-4" onSubmit={submitReview}>
            <h3 className="mb-3">Новый разбор{selectedEmployee ? `: ${selectedEmployee.full_name}` : ""}</h3>
            <label className="block mb-3">
              <span className="text-[11px] text-muted">Комментарий</span>
              <textarea
                className="input w-full mt-1 min-h-[80px]"
                required
                value={form.comment}
                onChange={(e) => setForm((f) => ({ ...f, comment: e.target.value }))}
              />
            </label>
            <label className="block mb-3">
              <span className="text-[11px] text-muted">Что обсудили</span>
              <textarea
                className="input w-full mt-1 min-h-[60px]"
                value={form.discussion}
                onChange={(e) => setForm((f) => ({ ...f, discussion: e.target.value }))}
              />
            </label>
            <label className="block mb-3">
              <span className="text-[11px] text-muted">Задачи (по одной на строку)</span>
              <textarea
                className="input w-full mt-1 min-h-[80px]"
                placeholder={"Переслушать звонки\nОбновить скрипт"}
                value={form.tasks}
                onChange={(e) => setForm((f) => ({ ...f, tasks: e.target.value }))}
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Сохранение…" : "Сохранить разбор"}
            </button>
          </form>
        )}

        {error && <div className="text-error mb-3">{error}</div>}

        <div className="card card-pad">
          {loading ? (
            <p className="text-secondary">Загрузка…</p>
          ) : reviews.length === 0 ? (
            <p className="text-secondary">Разборов пока нет</p>
          ) : (
            <table className="dash-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Сотрудник</th>
                  <th>Комментарий</th>
                  <th>Задачи</th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((r) => (
                  <tr key={r.id}>
                    <td>{formatDate(r.created_at)}</td>
                    <td>
                      <div>{r.employee_name}</div>
                      <div className="text-muted text-[11px]">{r.workspace_name}</div>
                    </td>
                    <td>
                      <div>{r.comment}</div>
                      {r.discussion && (
                        <div className="text-secondary text-[11px] mt-1">{r.discussion}</div>
                      )}
                      {r.client_name && (
                        <div className="text-[11px] mt-1">Клиент: {r.client_name}</div>
                      )}
                    </td>
                    <td>
                      <div className="text-[11px] text-muted mb-1">
                        {r.tasks_done}/{r.tasks_total} выполнено
                      </div>
                      <ul className="space-y-1">
                        {r.tasks.map((t) => (
                          <li key={t.id} className="flex items-center gap-2 text-[12px]">
                            <span
                              className={
                                t.status === "done"
                                  ? "badge badge-ok"
                                  : t.status === "in_progress"
                                    ? "badge badge-warn"
                                    : "badge"
                              }
                            >
                              {STATUS_LABELS[t.status] ?? t.status}
                            </span>
                            {t.title}
                          </li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
