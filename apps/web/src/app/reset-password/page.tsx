"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { confirmPasswordReset } from "@/lib/api";
import { AmbientBackground } from "@/components/AppShell";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const uid = searchParams.get("uid") ?? "";
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!uid || !token) {
      setError("Недействительная ссылка для сброса пароля.");
      return;
    }
    if (password !== confirm) {
      setError("Пароли не совпадают.");
      return;
    }
    setLoading(true);
    try {
      await confirmPasswordReset({ uid, token, new_password: password });
      router.replace("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка сброса пароля");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="flex flex-col gap-3" onSubmit={onSubmit}>
      <label className="text-[11px] uppercase tracking-wide text-muted">
        Новый пароль
        <input
          className="input mt-1.5"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
        />
      </label>
      <label className="text-[11px] uppercase tracking-wide text-muted">
        Подтвердите пароль
        <input
          className="input mt-1.5"
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
          minLength={8}
        />
      </label>
      {error && <p className="text-xs text-status-error">{error}</p>}
      <button className="btn-primary mt-1 w-full" type="submit" disabled={loading}>
        {loading ? "Сохранение…" : "Сохранить пароль"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
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
            <p className="mb-4 text-center text-xs text-muted">Задайте новый пароль для аккаунта.</p>
            <Suspense fallback={<p className="text-xs text-muted">Загрузка…</p>}>
              <ResetPasswordForm />
            </Suspense>
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
