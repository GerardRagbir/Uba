"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthCard } from "@/components/AuthCard";
import { Button, Field, Notice, type NoticeState } from "@/components/ui";
import { api, messageFrom, type User } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState<NoticeState>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const user = await api<User>("/auth/login", { method: "POST", body: { username, password } });
      router.replace(`/${user.role}`);
    } catch (error) {
      setNotice({ kind: "error", text: messageFrom(error) });
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Log in">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
        <Notice notice={notice} />
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Logging in…" : "Log in"}
        </Button>
      </form>
      <div className="mt-4 flex justify-between text-sm">
        <Link href="/register" className="font-semibold text-slate-700 underline decoration-amber-400 decoration-2 underline-offset-4 hover:text-slate-950">Create an account</Link>
        <Link href="/forgot-password" className="font-semibold text-slate-700 underline decoration-amber-400 decoration-2 underline-offset-4 hover:text-slate-950">Forgot password?</Link>
      </div>
    </AuthCard>
  );
}
