"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { requestPasswordReset } from "@/lib/api";
import { AmbientBackground } from "@/components/AppShell";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const data = await requestPasswordReset(email);
      setSuccess(data.detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <AmbientBackground />
      <div className="relative z-[1] flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-[420px]">
          <div className="card p-7">
            <div className="mb-5 flex items-center justify-center gap-2.5 text-sm font-bold">
              <div className="h-8 w-8 rounded-[11px] bg-accent-cyan/10" />
              AI Sales OS
            </div>
            <p className="mb-4 text-center text-xs text-muted">
              Введите email — мы отправим ссылку для сброса пароля.
            </p>
            <form className="flex flex-col gap-3" onSubmit={onSubmit}>
              <label className="text-[11px] uppercase tracking-wide text-muted">
                Email
                <input
                  className="input mt-1.5"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </label>
              {error && <p className="text-xs text-status-error">{error}</p>}
              {success && <p className="text-xs text-status-success">{success}</p>}
              <button className="btn-primary mt-1 w-full" type="submit" disabled={loading}>
                {loading ? "Отправка…" : "Отправить ссылку"}
              </button>
            </form>
          </div>
          <p className="mt-3 text-center text-[11px] text-muted">
            <Link className="text-accent-cyan hover:underline" href="/login">
              Вернуться ко входу
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
