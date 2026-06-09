"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchManagerClients, type ClientToReview } from "@/lib/dashboard";

export function ClientsToReviewView() {
  const [clients, setClients] = useState<ClientToReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchManagerClients();
      setClients(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    window.addEventListener("focus", load);
    return () => window.removeEventListener("focus", load);
  }, [load]);

  return (
    <div className="manager-layout">
      <div className="manager-main">
        <header>
          <h1 className="page-title">Клиенты к разбору</h1>
          <p className="page-subtitle">Клиенты с просадкой качества или отклонением от нормы</p>
        </header>

        {error && !clients.length ? (
          <div className="card card-pad">
            <p className="text-error mb-3">{error}</p>
            <button type="button" className="btn-secondary" onClick={load} disabled={loading}>
              {loading ? "Загрузка…" : "Повторить"}
            </button>
          </div>
        ) : (
          <div className="card card-pad">
            <div className="section-head">
              <h3>Очередь разборов</h3>
              <span className="badge badge-warn">{clients.length} клиента</span>
            </div>
            {loading && clients.length === 0 ? (
              <p className="text-secondary">Загрузка…</p>
            ) : clients.length === 0 ? (
              <p className="text-secondary">Все клиенты из очереди разобраны</p>
            ) : (
              <table className="dash-table">
                <thead>
                  <tr>
                    <th>Клиент</th>
                    <th>Сотрудник</th>
                    <th>Причина</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((c) => (
                    <tr key={c.id}>
                      <td>{c.client_name}</td>
                      <td>{c.employee_name}</td>
                      <td>{c.reason}</td>
                      <td className="space-x-2">
                        <Link
                          href={`/manager/reviews?employee_id=${c.employee_id}&workspace_id=${c.workspace_id}&client_id=${c.id}`}
                          className="link-btn"
                        >
                          Разбор
                        </Link>
                        <Link
                          href={`/manager/agent?client_id=${c.id}&client_name=${encodeURIComponent(c.client_name)}&client_note=${encodeURIComponent(c.reason)}`}
                          className="link-btn"
                        >
                          AI
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      <aside className="insight-panel">
        <div className="card insight-card card-pad">
          <h4>Быстрая сводка</h4>
          <div className="insight-item">
            <strong className="text-warning">{clients.length}</strong> клиента в очереди
          </div>
          <div className="insight-item">Разборы связаны с историей (PAGE-004)</div>
        </div>
      </aside>
    </div>
  );
}
