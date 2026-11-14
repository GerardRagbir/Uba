"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { AuthCard } from "@/components/AuthCard";
import { Button, Field, Notice, type NoticeState } from "@/components/ui";
import { api, messageFrom } from "@/lib/api";

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState<NoticeState>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    // The token arrives in the link from the email: /reset-password?token=...
    const token = new URLSearchParams(window.location.search).get("token") ?? "";
    setBusy(true);
    setNotice(null);
    try {
      const result = await api<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: { token, new_password: password },
      });
      setNotice({ kind: "ok", text: result.message });
      setDone(true);
    } catch (error) {
      setNotice({ kind: "error", text: messageFrom(error) });
    }
    setBusy(false);
  }

  return (
    <AuthCard title="Choose a new password">
      <form onSubmit={submit} className="space-y-4">
        <Field label="New password (at least 8 characters)" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required minLength={8} disabled={done} />
        <Notice notice={notice} />
        {!done && (
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Saving…" : "Change password"}
          </Button>
        )}
      </form>
      <p className="mt-4 text-sm">
        <Link href="/login" className="font-semibold text-slate-700 underline decoration-amber-400 decoration-2 underline-offset-4 hover:text-slate-950">Back to log in</Link>
      </p>
    </AuthCard>
  );
}
