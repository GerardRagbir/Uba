"use client";

import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { Logo, glass } from "@/components/ui";
import { api, type User } from "@/lib/api";

// The frame around every logged-in page: logo on the left, welcome menu
// with "Log out" on the right.
export function Shell({ subtitle, user, children }: { subtitle: string; user: User | null; children: ReactNode }) {
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  async function logout() {
    await api("/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-5">
      <header className={`${glass} relative z-20 mb-6 flex items-center justify-between px-5 py-3`}>
        <Logo subtitle={subtitle} />
        {user && (
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              aria-expanded={menuOpen}
              className="flex items-center gap-2 rounded-full py-1.5 pl-1.5 pr-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-900/5"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-bold uppercase text-white">
                {user.username.slice(0, 1)}
              </span>
              <span>
                <span className="hidden sm:inline">Welcome, </span>
                {user.username}
              </span>
              <span aria-hidden="true" className={`text-xs transition ${menuOpen ? "rotate-180" : ""}`}>▾</span>
            </button>
            {menuOpen && (
              <div className="absolute right-0 mt-2 w-40 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-xl">
                <button onClick={logout} className="block w-full px-4 py-2.5 text-left text-sm font-medium hover:bg-slate-100">
                  Log out
                </button>
              </div>
            )}
          </div>
        )}
      </header>
      {children}
    </div>
  );
}

export function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className={`${glass} px-5 py-3 text-sm font-medium text-slate-600`}>Loading…</p>
    </div>
  );
}
