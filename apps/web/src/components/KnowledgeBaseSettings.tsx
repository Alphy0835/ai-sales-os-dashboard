"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchMe } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import {
  createKnowledgeArticle,
  deleteKnowledgeArticle,
  fetchKnowledgeArticles,
  type KnowledgeArticle,
} from "@/lib/agent-api";

const CATEGORIES = [
  { value: "product", label: "Продукт" },
  { value: "objection", label: "Отработка" },
  { value: "infopovod", label: "Инфопovod" },
  { value: "case", label: "Кейс" },
  { value: "other", label: "Другое" },
];

const ACCESS = [
  { value: "all", label: "Все" },
  { value: "manager", label: "Только руководители" },
  { value: "employee", label: "Только сотрудники" },
];

export function KnowledgeBaseSettingsView() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [canEdit, setCanEdit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    title: "",
    category: "product",
    access_level: "all",
    tags: "",
    content: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    const token = getAccessToken();
    const [list, me] = await Promise.all([
      fetchKnowledgeArticles(),
      token ? fetchMe(token) : Promise.resolve(null),
    ]);
    setArticles(list.results);
    setCanEdit(me?.permissions.settings === "edit");
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;
    await createKnowledgeArticle(form);
    setForm({ title: "", category: "product", access_level: "all", tags: "", content: "" });
    await load();
  };

  return (
    <div className="card card-pad">
      {canEdit && (
        <form className="mb-4" onSubmit={onCreate}>
          <h3 className="mb-3">Новый материал</h3>
          <div className="grid gap-3 md:grid-cols-2 mb-3">
            <input className="input" placeholder="Название" required value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
            <select className="input" value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <textarea className="input w-full mb-3 min-h-[80px]" placeholder="Содержание" required value={form.content} onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))} />
          <div className="flex gap-3 mb-3">
            <input className="input flex-1" placeholder="Теги через запятую" value={form.tags} onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))} />
            <select className="input" value={form.access_level} onChange={(e) => setForm((f) => ({ ...f, access_level: e.target.value }))}>
              {ACCESS.map((a) => (
                <option key={a.value} value={a.value}>{a.label}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary">Добавить</button>
        </form>
      )}
      {loading ? (
        <p className="text-secondary">Загрузка…</p>
      ) : (
        <table className="dash-table">
          <thead>
            <tr>
              <th>Материал</th>
              <th>Категория</th>
              <th>Доступ</th>
              {canEdit && <th />}
            </tr>
          </thead>
          <tbody>
            {articles.map((a) => (
              <tr key={a.id}>
                <td><div>{a.title}</div><div className="text-[11px] text-muted">{a.content.slice(0, 80)}…</div></td>
                <td>{a.category_label}</td>
                <td>{a.access_label}</td>
                {canEdit && (
                  <td><button type="button" className="link-btn" onClick={() => deleteKnowledgeArticle(a.id).then(load)}>Удалить</button></td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
