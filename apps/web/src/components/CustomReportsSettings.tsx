"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchMe } from "@/lib/api";
import {
  createCustomReport,
  deleteCustomReport,
  fetchCustomReports,
  type CustomReport,
} from "@/lib/analytics-api";
import { SettingsAddPanel, SettingsPanelShell } from "@/components/SettingsPanelShell";

export function CustomReportsSettingsView() {
  const [reports, setReports] = useState<CustomReport[]>([]);
  const [canEdit, setCanEdit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: "", description: "" });

  const load = useCallback(async () => {
    setLoading(true);
    const [list, me] = await Promise.all([fetchCustomReports(), fetchMe()]);
    setReports(list.results);
    setCanEdit(me?.permissions.settings === "edit");
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;
    await createCustomReport(form);
    setForm({ title: "", description: "" });
    await load();
  };

  return (
    <SettingsPanelShell
      footer={
        <SettingsAddPanel label="Новый кастомный отчёт" canEdit={canEdit} onSubmit={onCreate}>
          <input
            className="input w-full mb-3"
            placeholder="Название"
            required
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
          <textarea
            className="input w-full min-h-[100px]"
            placeholder="Опишите отчёт простым языком: что анализировать, на каких этапах воронки"
            required
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </SettingsAddPanel>
      }
    >
      {loading ? (
        <p className="text-secondary">Загрузка…</p>
      ) : reports.length === 0 ? (
        <p className="text-secondary">Кастомных отчётов пока нет</p>
      ) : (
        <table className="dash-table">
          <thead>
            <tr>
              <th>Отчёт</th>
              <th>Фокус</th>
              {canEdit && <th />}
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <tr key={r.id}>
                <td>
                  <div>{r.title}</div>
                  <div className="text-[11px] text-muted">{r.description.slice(0, 100)}…</div>
                </td>
                <td className="text-[12px] text-secondary">
                  {(r.structured_query.focus_stages as string[] | undefined)?.join(", ") || "—"}
                </td>
                {canEdit && (
                  <td>
                    <button type="button" className="link-btn" onClick={() => deleteCustomReport(r.id).then(load)}>
                      Удалить
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </SettingsPanelShell>
  );
}
