"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login } from "@/lib/api";
import { homeRouteForRole, saveSession } from "@/lib/auth";
import { AmbientBackground } from "@/components/AppShell";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("manager@demo.local");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await login(email, password);
      saveSession(data.access, data.refresh, data.user);
      router.replace(homeRouteForRole(data.user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
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
              <label className="text-[11px] uppercase tracking-wide text-muted">
                Пароль
                <input
                  className="input mt-1.5"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </label>
              {error && <p className="text-xs text-status-error">{error}</p>}
              <button className="btn-primary mt-1 w-full" type="submit" disabled={loading}>
                {loading ? "Вход…" : "Войти"}
              </button>
            </form>
          </div>
          <p className="mt-3 text-center text-[11px] text-muted">
            Demo: manager@demo.local / employee@demo.local — пароль demo1234
          </p>
        </div>
      </div>
    </>
  );
}
