"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchMe } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import {
  createQualityCriterion,
  deleteQualityCriterion,
  fetchQualityCriteria,
  updateQualityCriterion,
  type QualityCriterion,
} from "@/lib/analytics-api";

const STAGES = [
  { value: "greeting", label: "Приветствие" },
  { value: "discovery", label: "Выявление потребности" },
  { value: "presentation", label: "Презентация" },
  { value: "objections", label: "Возражения" },
  { value: "closing", label: "Закрытие" },
];

export function QualityCriteriaSettingsView() {
  const [criteria, setCriteria] = useState<QualityCriterion[]>([]);
  const [canEdit, setCanEdit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", funnel_stage: "greeting", keywords: "", description: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = getAccessToken();
      const [list, me] = await Promise.all([
        fetchQualityCriteria(),
        token ? fetchMe(token) : Promise.resolve(null),
      ]);
      setCriteria(list.results);
      setCanEdit(me?.permissions.settings === "edit");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;
    try {
      await createQualityCriterion(form);
      setForm({ name: "", funnel_stage: "greeting", keywords: "", description: "" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    }
  };

  const onDelete = async (id: string) => {
    if (!canEdit) return;
    await deleteQualityCriterion(id);
    await load();
  };

  const onToggle = async (item: QualityCriterion) => {
    if (!canEdit) return;
    await updateQualityCriterion(item.id, { is_active: !item.is_active });
    await load();
  };

  return (
    <>
      <header>
        <h1 className="page-title">Настройки</h1>
        <p className="page-subtitle">Критерии оценки качества для AI-аналитики</p>
      </header>

      {error && <div className="text-error mb-3">{error}</div>}

      {canEdit && (
        <form className="card card-pad mb-4" onSubmit={onCreate}>
          <h3 className="mb-3">Новый критерий</h3>
          <div className="grid gap-3 md:grid-cols-2 mb-3">
            <label className="block">
              <span className="text-[11px] text-muted">Название</span>
              <input className="input w-full mt-1" required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
            </label>
            <label className="block">
              <span className="text-[11px] text-muted">Этап воронки</span>
              <select className="input w-full mt-1" value={form.funnel_stage} onChange={(e) => setForm((f) => ({ ...f, funnel_stage: e.target.value }))}>
                {STAGES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </label>
          </div>
          <label className="block mb-3">
            <span className="text-[11px] text-muted">Ключевые слова (через запятую)</span>
            <input className="input w-full mt-1" value={form.keywords} onChange={(e) => setForm((f) => ({ ...f, keywords: e.target.value }))} />
          </label>
          <button type="submit" className="btn btn-primary">Добавить</button>
        </form>
      )}

      <div className="card card-pad">
        {loading ? (
          <p className="text-secondary">Загрузка…</p>
        ) : criteria.length === 0 ? (
          <p className="text-secondary">Критериев пока нет</p>
        ) : (
          <table className="dash-table">
            <thead>
              <tr>
                <th>Критерий</th>
                <th>Этап</th>
                <th>Ключевые слова</th>
                <th>Активен</th>
                {canEdit && <th />}
              </tr>
            </thead>
            <tbody>
              {criteria.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.stage_label}</td>
                  <td className="text-[12px]">{c.keywords}</td>
                  <td>
                    {canEdit ? (
                      <button type="button" className="chip" onClick={() => onToggle(c)}>
                        {c.is_active ? "Да" : "Нет"}
                      </button>
                    ) : (
                      c.is_active ? "Да" : "Нет"
                    )}
                  </td>
                  {canEdit && (
                    <td>
                      <button type="button" className="link-btn" onClick={() => onDelete(c.id)}>Удалить</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
