"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { register } from "@/lib/api";
import { homeRouteForRole, saveSession } from "@/lib/auth";
import { AmbientBackground } from "@/components/AppShell";

export default function RegisterPage() {
  const router = useRouter();
  const [inviteCode, setInviteCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await register({
        invite_code: inviteCode,
        email,
        password,
        full_name: fullName,
      });
      saveSession(data.user);
      router.replace(homeRouteForRole(data.user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка регистрации");
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
                Код приглашения
                <input
                  className="input mt-1.5"
                  type="text"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  required
                />
              </label>
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
              <label className="text-[11px] uppercase tracking-wide text-muted">
                Полное имя
                <input
                  className="input mt-1.5"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </label>
              {error && <p className="text-xs text-status-error">{error}</p>}
              <button className="btn-primary mt-1 w-full" type="submit" disabled={loading}>
                {loading ? "Регистрация…" : "Зарегистрироваться"}
              </button>
            </form>
          </div>
          <p className="mt-3 text-center text-[11px] text-muted">
            <Link className="text-accent-cyan hover:underline" href="/login">
              Уже есть аккаунт? Войти
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
