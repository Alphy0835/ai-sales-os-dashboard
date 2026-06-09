"use client";

import { useState } from "react";
import { sendAgentMessage, type AgentMessage, type AgentSession } from "@/lib/agent-api";

type Props = {
  variant: "manager" | "employee";
};

export function AgentChatView({ variant }: Props) {
  const [session, setSession] = useState<AgentSession | null>(null);
  const [clientName, setClientName] = useState("");
  const [clientNote, setClientNote] = useState("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(true);

  const messages = session?.messages ?? [];

  const onSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await sendAgentMessage(variant, {
        message: input,
        session_id: session?.id,
        client_name: clientName,
        client_note: clientNote,
      });
      setSession(result);
      setInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setLoading(false);
    }
  };

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant") as AgentMessage | undefined;

  return (
    <div className="manager-layout no-insight">
      <div className="manager-main">
        <header>
          <h1 className="page-title">AI-агент</h1>
          <p className="page-subtitle">
            {variant === "manager" ? "Стратегия и тактика с опорой на базу знаний" : "Помощь по продукту и отработкам"}
          </p>
        </header>

        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="card card-pad">
            <h3 className="mb-3">Контекст клиента</h3>
            <label className="block mb-3 text-[11px] text-muted">
              Клиент
              <input className="input w-full mt-1" value={clientName} onChange={(e) => setClientName(e.target.value)} placeholder="ООО «Вектор»" />
            </label>
            <label className="block text-[11px] text-muted">
              Комментарий
              <textarea className="input w-full mt-1 min-h-[100px]" value={clientNote} onChange={(e) => setClientNote(e.target.value)} placeholder="Что обсудили, риски…" />
            </label>
          </aside>

          <div className="card card-pad flex flex-col min-h-[420px]">
            <div className="flex-1 space-y-3 overflow-y-auto mb-4 max-h-[360px]">
              {messages.length === 0 && <p className="text-secondary">Задайте вопрос — ответ будет с опорой на RAG-базу.</p>}
              {messages.map((m) => (
                <div key={m.id} className={m.role === "user" ? "text-right" : ""}>
                  <div className={`inline-block rounded-lg px-3 py-2 text-[13px] max-w-[90%] ${m.role === "user" ? "bg-accent-cyan/10" : "bg-white/5"}`}>
                    {m.content}
                  </div>
                </div>
              ))}
            </div>

            {lastAssistant && lastAssistant.sources.length > 0 && (
              <div className="mb-3 border-t border-white/5 pt-3">
                <button type="button" className="link-btn mb-2" onClick={() => setShowSources((v) => !v)}>
                  {showSources ? "Скрыть" : "Показать"} источники RAG ({lastAssistant.sources.length})
                </button>
                {showSources && (
                  <ul className="text-[11px] text-muted space-y-1">
                    {lastAssistant.sources.map((s) => (
                      <li key={s.id}>• {s.title}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {error && <div className="text-error mb-2">{error}</div>}

            <form className="flex gap-2" onSubmit={onSend}>
              <input
                className="input flex-1"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ваш вопрос…"
                disabled={loading}
              />
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "…" : "Отправить"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
