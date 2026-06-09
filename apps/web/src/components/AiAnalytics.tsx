"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchMe } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { fetchManagerDashboard } from "@/lib/dashboard";
import { fetchAnalyticsReports, fetchCustomReports, runAnalyticsReport, type AnalyticsReport, type CustomReport } from "@/lib/analytics-api";

const TEMPLATES = [
  { value: "standard_quality", label: "Стандартный отчёт по качеству" },
  { value: "funnel_dynamics", label: "Динамика по этапам воронки" },
];

export function AiAnalyticsView() {
  const [workspaceId, setWorkspaceId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [template, setTemplate] = useState("standard_quality");
  const [customReportId, setCustomReportId] = useState("");
  const [customReports, setCustomReports] = useState<CustomReport[]>([]);
  const [workspaces, setWorkspaces] = useState<Array<{ id: string; name: string }>>([]);
  const [employees, setEmployees] = useState<Array<{ id: string; full_name: string }>>([]);
  const [canRun, setCanRun] = useState(false);
  const [report, setReport] = useState<AnalyticsReport | null>(null);
  const [history, setHistory] = useState<AnalyticsReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = getAccessToken();
      const [dash, reports, custom, me] = await Promise.all([
        fetchManagerDashboard({ workspace_id: workspaceId || undefined }),
        fetchAnalyticsReports(),
        fetchCustomReports().catch(() => ({ count: 0, results: [] as CustomReport[] })),
        token ? fetchMe(token) : Promise.resolve(null),
      ]);
      setWorkspaces(dash.filters.workspaces);
      setEmployees(dash.filters.employees);
      setHistory(reports.results);
      setCustomReports(custom.results);
      const level = me?.permissions.analytics;
      setCanRun(level === "run" || level === "edit");
      if (!workspaceId && dash.filters.workspaces[0]) {
        setWorkspaceId(dash.filters.workspaces[0].id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    load();
  }, [load]);

  const onRun = async () => {
    if (!workspaceId) return;
    setRunning(true);
    setError(null);
    try {
      const result = await runAnalyticsReport({
        workspace_id: workspaceId,
        employee_id: employeeId || undefined,
        ...(customReportId
          ? { custom_report_id: customReportId }
          : { template }),
      });
      setReport(result);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось запустить отчёт");
      setReport(null);
    } finally {
      setRunning(false);
    }
  };

  if (loading && history.length === 0) {
    return <div className="text-secondary">Загрузка…</div>;
  }

  return (
    <div className="manager-layout">
      <div className="manager-main">
        <header>
          <h1 className="page-title">AI-аналитика</h1>
          <p className="page-subtitle">Стандартные и кастомные отчёты по качеству общения на основе транскрипций</p>
        </header>

        <div className="card card-pad mb-4">
          <div className="filters-row flex flex-wrap gap-3 items-end">
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Подразделение
              <select className="input" value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
                {workspaces.map((ws) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Сотрудник
              <select className="input" value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
                <option value="">Все в подразделении</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.full_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Шаблон
              <select
                className="input"
                value={customReportId ? `custom:${customReportId}` : template}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value.startsWith("custom:")) {
                    setCustomReportId(value.slice(7));
                  } else {
                    setCustomReportId("");
                    setTemplate(value);
                  }
                }}
              >
                {TEMPLATES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
                {customReports.length > 0 && (
                  <optgroup label="Кастомные отчёты">
                    {customReports.map((r) => (
                      <option key={r.id} value={`custom:${r.id}`}>
                        {r.title}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </label>
            {canRun ? (
              <button type="button" className="btn btn-primary ml-auto" disabled={running} onClick={onRun}>
                {running ? "Анализ…" : "Запустить анализ"}
              </button>
            ) : (
              <span className="text-muted text-[12px] ml-auto">Нужно право analytics: run</span>
            )}
          </div>
        </div>

        {error && <div className="text-error mb-3">{error}</div>}

        {report && report.status === "completed" && (
          <div className="card card-pad mb-4">
            <div className="section-head mb-3">
              <h3>Канвас отчёта</h3>
              {report.canvas.overall_score != null && (
                <span className="badge badge-ok">{report.canvas.overall_score}%</span>
              )}
            </div>
            <p className="mb-4">{report.summary_text}</p>
            <div className="grid gap-3 md:grid-cols-2 mb-4">
              {report.canvas.stages.map((stage) => (
                <div key={stage.stage} className="card card-pad">
                  <div className="kpi-label">{stage.label}</div>
                  <div className="kpi-value">{stage.score ?? "—"}</div>
                </div>
              ))}
            </div>
            {report.canvas.recommendations.length > 0 && (
              <div className="mb-3">
                <h4 className="mb-2">Рекомендации к разбору</h4>
                <ul className="space-y-2">
                  {report.canvas.recommendations.map((rec) => (
                    <li key={rec.text} className="flex items-center justify-between gap-2">
                      <span>{rec.text}</span>
                      <Link href="/manager/reviews" className="link-btn">
                        Вынести на разбор
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="card card-pad">
          <div className="section-head mb-3">
            <h3>История отчётов</h3>
          </div>
          {history.length === 0 ? (
            <p className="text-secondary">Отчётов пока нет</p>
          ) : (
            <table className="dash-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Шаблон</th>
                  <th>Объект</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r) => (
                  <tr key={r.id}>
                    <td>{new Date(r.created_at).toLocaleDateString("ru-RU")}</td>
                    <td>{r.template_label}</td>
                    <td>{r.employee_name ?? r.workspace_name}</td>
                    <td>{r.status === "completed" ? "Готов" : r.error_message || r.status}</td>
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
