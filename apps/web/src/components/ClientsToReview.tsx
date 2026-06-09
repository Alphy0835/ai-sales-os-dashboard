"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchManagerClients, type ClientToReview } from "@/lib/dashboard";

export function ClientsToReviewView() {
  const [clients, setClients] = useState<ClientToReview[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchManagerClients()
      .then((res) => setClients(res.results))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="manager-layout">
      <div className="manager-main">
        <header>
          <h1 className="page-title">Клиенты к разбору</h1>
          <p className="page-subtitle">Клиенты с просадкой качества или отклонением от нормы</p>
        </header>

        <div className="card card-pad">
          <div className="section-head">
            <h3>Очередь разборов</h3>
            <span className="badge badge-warn">{clients.length} клиента</span>
          </div>
          {loading ? (
            <p className="text-secondary">Загрузка…</p>
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
                    <td>
                      <Link href="/manager/reviews" className="link-btn">
                        Разбор
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <aside className="insight-panel">
        <div className="card insight-card card-pad">
          <h4>Быстрая сводка</h4>
          <div className="insight-item">
            <strong className="text-warning">{clients.length}</strong> клиента в очереди
          </div>
          <div className="insight-item">Разборы — STAGE-004</div>
        </div>
      </aside>
    </div>
  );
}
