"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { AuthCard } from "@/components/AuthCard";
import { Button, Field, Notice, type NoticeState } from "@/components/ui";
import { api, messageFrom } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [notice, setNotice] = useState<NoticeState>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const result = await api<{ message: string }>("/auth/forgot-password", { method: "POST", body: { email: email.trim() } });
      setNotice({ kind: "ok", text: result.message });
    } catch (error) {
      setNotice({ kind: "error", text: messageFrom(error) });
    }
    setBusy(false);
  }

  return (
    <AuthCard title="Forgot password">
      <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-slate-600">Enter the email on your account and we will send you a link to choose a new password.</p>
        <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
        <Notice notice={notice} />
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Sending…" : "Send reset link"}
        </Button>
      </form>
      <p className="mt-4 text-sm">
        <Link href="/login" className="font-semibold text-slate-700 underline decoration-amber-400 decoration-2 underline-offset-4 hover:text-slate-950">Back to log in</Link>
      </p>
    </AuthCard>
  );
}
