import type { ReactNode } from "react";

import { Logo, glass } from "@/components/ui";

// The centred card used by the login, register and password pages.
export function AuthCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <section className={`${glass} w-full max-w-sm p-7`}>
        <Logo subtitle="Taxi booking across Trinidad" />
        <h1 className="mb-5 mt-6 text-xl font-bold tracking-tight">{title}</h1>
        {children}
      </section>
    </main>
  );
}
