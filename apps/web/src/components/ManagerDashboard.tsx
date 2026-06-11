"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  fetchEmployeeDashboard,
  fetchManagerDashboard,
  type ManagerDashboard,
  type MetricPeriod,
} from "@/lib/dashboard";
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

function statusBadge(status: string) {
  if (status === "ok") return <span className="badge badge-ok">Норма</span>;
  if (status === "warn") return <span className="badge badge-warn">Контроль</span>;
  return <span className="badge badge-bad">Риск</span>;
}

function sourceBadge(status: string) {
  if (status === "connected") return <span className="badge badge-ok">OK</span>;
  if (status === "degraded") return <span className="badge badge-warn">Частично</span>;
  return <span className="badge badge-bad">Нет данных</span>;
}

function sourceDot(status: string) {
  if (status === "connected") return "dot-ok";
  if (status === "degraded") return "dot-warn";
  return "dot-bad";
}

export function ManagerDashboardView({ variant = "manager" }: { variant?: "manager" | "employee" }) {
  const isManager = variant === "manager";
  const [period, setPeriod] = useState<MetricPeriod>("today");
  const [workspaceId, setWorkspaceId] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [data, setData] = useState<ManagerDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dash = isManager
        ? await fetchManagerDashboard({
            workspace_id: workspaceId || undefined,
            user_id: userId || undefined,
          })
        : await fetchEmployeeDashboard();
      setData(dash);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [workspaceId, userId, isManager]);

  const onTaskStatus = async (taskId: string, status: EmployeeTask["status"]) => {
    setUpdatingTaskId(taskId);
    try {
      await updateEmployeeTask(taskId, status);
      await load();
    } finally {
      setUpdatingTaskId(null);
    }
  };

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !data) {
    return <div className="text-secondary">Загрузка дашборда…</div>;
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
  const maxTrend = Math.max(...(data.trend?.values ?? [0]), 1);
  const workspaceLabel = data.filters.workspaces[0]?.name ?? "—";
  const employeeLabel = data.filters.employees[0]?.full_name ?? "—";
  const personalMetrics = data.employees[0];
  const growthItems = data.attention.items ?? [];
  const managerTasks = data.tasks ?? [];

  return (
    <div className="manager-layout">
      <div className="manager-main">
        <header className="topbar">
          <div>
            <div className="text-muted text-[11px]">Home / Dashboard</div>
            <h1 className="page-title">Дашборд</h1>
          </div>
          <select
            value={isManager ? workspaceId : data.filters.workspace_id ?? ""}
            onChange={(e) => setWorkspaceId(e.target.value)}
            aria-label="Подразделение"
            disabled={!isManager}
          >
            {isManager ? (
              <>
                <option value="">Все подразделения</option>
                {data.filters.workspaces.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </>
            ) : (
              <option value={data.filters.workspace_id ?? ""}>{workspaceLabel}</option>
            )}
          </select>
          <select
            value={isManager ? userId : data.filters.user_id ?? ""}
            onChange={(e) => setUserId(e.target.value)}
            aria-label="Сотрудник"
            disabled={!isManager}
          >
            {isManager ? (
              <>
                <option value="">Все сотрудники</option>
                {data.filters.employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.full_name}
                  </option>
                ))}
              </>
            ) : (
              <option value={data.filters.user_id ?? ""}>{employeeLabel}</option>
            )}
          </select>
          <div className="chips">
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
        </header>

        {metrics.completeness !== "full" && (
          <div className="card card-pad text-[12px] text-warning">
            {metrics.completeness_reason ?? "Частичные данные — часть источников недоступна"}
          </div>
        )}

        <div className="row-top">
          <div className="card card-highlight card-pad">
            <div className="kpi-hero">
              <div className="kpi-ring">
                {data.hero.quality_available && data.hero.quality_score != null
                  ? `${Math.round(data.hero.quality_score)}%`
                  : "—"}
              </div>
              <div>
                <div className="kpi-label">Качество · {PERIOD_LABELS[period].toLowerCase()}</div>
                <div className="kpi-value">{data.hero.calls ?? 0} звонков</div>
                <div className={`kpi-delta ${(data.hero.calls ?? 0) >= data.hero.plan_calls ? "up" : "down"}`}>
                  план: {data.hero.plan_calls} звонков
                </div>
              </div>
            </div>
          </div>
          <div className="card card-pad">
            <div className="mini-metrics">
              <div>
                <div className="mini-ring">{metrics.metrics.deals?.value ?? 0}</div>
                <div className="kpi-label">Сделки</div>
              </div>
              <div>
                <div className="mini-ring">{metrics.metrics.meetings?.value ?? 0}</div>
                <div className="kpi-label">Встречи</div>
              </div>
            </div>
          </div>
          <div className="card card-pad">
            <div className="kpi-label">{isManager ? "Требует внимания" : "Зоны роста"}</div>
            {isManager ? (
              <p className="ai-text">{data.attention.text ?? "Показатели в норме"}</p>
            ) : growthItems.length > 0 ? (
              <ul className="space-y-2">
                {growthItems.map((item) => (
                  <li key={item.text} className="ai-text text-[12px]">
                    {item.author_name ? `${item.author_name}: ` : ""}
                    {item.text}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="ai-text">{data.attention.text ?? "Показатели в норме"}</p>
            )}
            {isManager && (
              <>
                <Link href="/manager/clients" className="btn-secondary inline-flex items-center">
                  Клиенты к разбору →
                </Link>
                <Link href="/manager/reviews" className="btn-secondary inline-flex items-center mt-2">
                  История разборов →
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="row-mid">
          <div className="card card-pad">
            <div className="section-head">
              <h3>Динамика звонков (7д)</h3>
            </div>
            <div className="chart-bars">
              {(data.trend?.values ?? []).map((v, i) => (
                <span
                  key={data.trend.labels[i] ?? i}
                  style={{ height: `${(v / maxTrend) * 100}%` }}
                  title={`${data.trend.labels[i]}: ${v}`}
                />
              ))}
            </div>
            {data.ai_summary?.text && (
              <p className="ai-text mt-3">AI: {data.ai_summary.text.slice(0, 120)}…</p>
            )}
          </div>
          <div className="card card-pad card-highlight">
            {data.ai_summary ? (
              <>
                <div className="flex justify-between">
                  <span className="ai-badge">AI Recommendation</span>
                  <span className="text-muted text-[10px]">Confidence {data.ai_summary.confidence}%</span>
                </div>
                <p className="ai-text">{data.ai_summary.text}</p>
                <div className="mb-3">
                  {data.ai_summary.sources.map((s) => (
                    <span key={s} className="source-tag">
                      {s}
                    </span>
                  ))}
                </div>
                {isManager && (
                  <Link href="/manager/clients" className="btn-secondary">
                    Suggested Action: Разбор →
                  </Link>
                )}
              </>
            ) : (
              <p className="ai-text">Недостаточно данных для AI-сводки. Отображаются числовые метрики.</p>
            )}
          </div>
        </div>

        <div className="row-bot">
          <div className="card card-pad">
            <div className="section-head">
              <h3>{isManager ? "Сотрудники · показатели" : "Мои показатели"}</h3>
            </div>
            {isManager ? (
              <table className="dash-table">
                <thead>
                  <tr>
                    <th>Сотрудник</th>
                    <th>Качество</th>
                    <th>Звонки</th>
                    <th>Статус</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {data.employees.map((emp) => (
                    <tr key={emp.id}>
                      <td>{emp.full_name}</td>
                      <td>{emp.quality_score != null ? `${Math.round(emp.quality_score)}%` : "—"}</td>
                      <td>{emp.calls}</td>
                      <td>{statusBadge(emp.status)}</td>
                      <td>
                        <Link
                          href={`/manager/reviews?employee_id=${emp.id}`}
                          className="link-btn"
                        >
                          Разбор
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : personalMetrics ? (
              <table className="dash-table">
                <thead>
                  <tr>
                    <th>Качество</th>
                    <th>Звонки</th>
                    <th>Сделки</th>
                    <th>Встречи</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      {personalMetrics.quality_score != null
                        ? `${Math.round(personalMetrics.quality_score)}%`
                        : "—"}
                    </td>
                    <td>{personalMetrics.calls}</td>
                    <td>{metrics.metrics.deals?.value ?? 0}</td>
                    <td>{metrics.metrics.meetings?.value ?? 0}</td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <p className="text-secondary">Нет данных за выбранный период</p>
            )}
          </div>
          <div className="card card-pad">
            <div className="section-head">
              <h3>Источники данных</h3>
            </div>
            {metrics.sources.map((s) => (
              <div key={s.id ?? s.source_type} className="source-row">
                <span>
                  <span className={`dot ${sourceDot(s.status)}`} />
                  {s.name}
                </span>
                {sourceBadge(s.status)}
              </div>
            ))}
          </div>
        </div>
      </div>

      <aside className="insight-panel">
        <div className="card insight-card card-pad">
          <h4>{isManager ? "Быстрая сводка" : "Задачи от руководителя"}</h4>
          {isManager ? (
            data.ai_summary?.highlights?.length ? (
              data.ai_summary.highlights.map((h) => (
                <div key={h.text} className="insight-item">
                  {h.text}
                </div>
              ))
            ) : (
              <div className="insight-item">Нет активных сигналов</div>
            )
          ) : managerTasks.length > 0 ? (
            managerTasks.map((task) => (
              <div key={task.id} className="insight-item">
                <div className="font-medium">{task.title}</div>
                <div className="text-[10px] text-muted mb-1">
                  {task.author_name} · {new Date(task.review_date).toLocaleDateString("ru-RU")}
                </div>
                <select
                  className="input mt-1"
                  value={task.status}
                  disabled={updatingTaskId === task.id}
                  onChange={(e) => onTaskStatus(task.id, e.target.value as EmployeeTask["status"])}
                >
                  {TASK_STATUS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            ))
          ) : (
            <div className="insight-item">Нет активных задач</div>
          )}
        </div>
        <div className="card insight-card card-pad">
          <h4>Completeness</h4>
          <div className="insight-item capitalize">{metrics.completeness}</div>
          <div className="insight-item">{metrics.completeness_reason ?? "Все источники доступны"}</div>
        </div>
      </aside>
    </div>
  );
}
