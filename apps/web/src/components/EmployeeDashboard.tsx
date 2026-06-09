"use client";

import { useEffect, useState } from "react";
import { fetchEmployeeDashboard, type MetricPeriod } from "@/lib/dashboard";

const PERIOD_LABELS: Record<MetricPeriod, string> = {
  today: "Сегодня",
  week: "Неделя",
  month: "Месяц",
};

export function EmployeeDashboardView() {
  const [period, setPeriod] = useState<MetricPeriod>("today");
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchEmployeeDashboard>> | null>(null);

  useEffect(() => {
    fetchEmployeeDashboard().then(setData);
  }, []);

  if (!data) return <div className="text-secondary">Загрузка…</div>;

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
      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(metrics.metrics).map(([key, m]) => (
          <div key={key} className="card card-pad">
            <div className="kpi-label">{m.label}</div>
            <div className="kpi-value">{m.available ? (m.value ?? 0) : "—"}</div>
            {!m.available && m.reason && <div className="text-warning text-[11px] mt-1">{m.reason}</div>}
          </div>
        ))}
      </div>
    </>
  );
}
