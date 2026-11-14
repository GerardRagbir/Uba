"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthCard } from "@/components/AuthCard";
import { Button, Field, Notice, SelectField, type NoticeState } from "@/components/ui";
import { api, messageFrom } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [role, setRole] = useState<"pax" | "driver">("pax");
  const [form, setForm] = useState({ username: "", email: "", name: "", password: "", phone: "", permit_no: "" });
  const [notice, setNotice] = useState<NoticeState>(null);
  const [busy, setBusy] = useState(false);

  function set(field: keyof typeof form) {
    return (event: { target: { value: string } }) => setForm({ ...form, [field]: event.target.value });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      await api("/auth/register", {
        method: "POST",
        body: {
          role,
          username: form.username.trim(),
          email: form.email.trim(),
          name: form.name.trim(),
          password: form.password,
          phone: role === "pax" ? form.phone.trim() || null : null,
          permit_no: role === "driver" ? form.permit_no.trim() || null : null,
        },
      });
      router.replace("/login");
    } catch (error) {
      setNotice({ kind: "error", text: messageFrom(error) });
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Create an account">
      <form onSubmit={submit} className="space-y-4">
        <SelectField label="Account type" value={role} onChange={(e) => setRole(e.target.value as "pax" | "driver")}>
          <option value="pax">Passenger</option>
          <option value="driver">Driver</option>
        </SelectField>
        <Field label="Username" value={form.username} onChange={set("username")} autoComplete="username" required minLength={3} />
        <Field label="Email" type="email" value={form.email} onChange={set("email")} autoComplete="email" required />
        <Field label="Full name" value={form.name} onChange={set("name")} autoComplete="name" required />
        <Field label="Password (at least 8 characters)" type="password" value={form.password} onChange={set("password")} autoComplete="new-password" required minLength={8} />
        {role === "pax" ? (
          <Field label="Phone number" value={form.phone} onChange={set("phone")} autoComplete="tel" />
        ) : (
          <Field label="Driver's permit number" value={form.permit_no} onChange={set("permit_no")} />
        )}
        <Notice notice={notice} />
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Creating…" : "Register"}
        </Button>
      </form>
      <p className="mt-4 text-sm">
        <Link href="/login" className="font-semibold text-slate-700 underline decoration-amber-400 decoration-2 underline-offset-4 hover:text-slate-950">Back to log in</Link>
      </p>
    </AuthCard>
  );
}
