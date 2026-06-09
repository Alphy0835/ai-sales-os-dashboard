"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchEmployeeDashboard, type MetricPeriod } from "@/lib/dashboard";
import { updateEmployeeTask, type EmployeeTask } from "@/lib/reviews";

const PERIOD_LABELS: Record<MetricPeriod, string> = {
  today: "Сегодня",
  week: "Неделя",
  month: "Месяц",
};

const TASK_STATUS: Array<{ value: EmployeeTask["status"]; label: string }> = [
  { value: "pending", label: "Ожидает" },
  { value: "in_progress", label: "В работе" },
  { value: "done", label: "Готово" },
];

export function EmployeeDashboardView() {
  const [period, setPeriod] = useState<MetricPeriod>("today");
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchEmployeeDashboard>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dash = await fetchEmployeeDashboard();
      setData(dash);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onTaskStatus = async (taskId: string, status: EmployeeTask["status"]) => {
    setUpdating(taskId);
    try {
      await updateEmployeeTask(taskId, status);
      await load();
    } finally {
      setUpdating(null);
    }
  };

  if (loading && !data) {
    return <div className="text-secondary">Загрузка…</div>;
  }

  if (error && !data) {
    return (
      <div className="card card-pad">
        <p className="text-error mb-3">{error}</p>
        <button type="button" className="btn-secondary" onClick={load} disabled={loading}>
          {loading ? "Загрузка…" : "Повторить"}
        </button>
      </div>
    );
  }

  if (!data) return null;

  const metrics = data.periods[period];

  return (
    <>
      <header>
        <h1 className="page-title">Личный дашборд</h1>
        <p className="page-subtitle">{data.hero.full_name}</p>
      </header>
      <div className="chips mb-4">
        {(Object.keys(PERIOD_LABELS) as MetricPeriod[]).map((p) => (
          <button
            key={p}
            type="button"
            className={`chip${period === p ? " on" : ""}`}
            onClick={() => setPeriod(p)}
          >
            {PERIOD_LABELS[p]}
          </button>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        {Object.entries(metrics.metrics).map(([key, m]) => (
          <div key={key} className="card card-pad">
            <div className="kpi-label">{m.label}</div>
            <div className="kpi-value">{m.available ? (m.value ?? 0) : "—"}</div>
            {!m.available && m.reason && <div className="text-warning text-[11px] mt-1">{m.reason}</div>}
          </div>
        ))}
      </div>

      <div className="card card-pad">
        <div className="section-head mb-3">
          <h3>Задачи от руководителя</h3>
          <span className="badge">{data.tasks.length}</span>
        </div>
        {data.tasks.length === 0 ? (
          <p className="text-secondary">Нет активных задач</p>
        ) : (
          <ul className="space-y-3">
            {data.tasks.map((task) => (
              <li key={task.id} className="flex flex-wrap items-center gap-3 border-b border-white/5 pb-3">
                <div className="flex-1 min-w-[200px]">
                  <div className="font-medium">{task.title}</div>
                  <div className="text-[11px] text-muted">
                    {task.author_name} · {new Date(task.review_date).toLocaleDateString("ru-RU")}
                  </div>
                </div>
                <select
                  className="input"
                  value={task.status}
                  disabled={updating === task.id}
                  onChange={(e) => onTaskStatus(task.id, e.target.value as EmployeeTask["status"])}
                >
                  {TASK_STATUS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
