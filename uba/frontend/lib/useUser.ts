"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, type Role, type User } from "./api";

// Finds out who is logged in. Sends visitors to /login, and sends a logged-in
// user who opened the wrong page to their own page.
//
// This is only for a pleasant experience. The real protection is on the
// server: every API route checks the role again.
export function useUser(role: Role): User | null {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<User>("/auth/me")
      .then((me) => {
        if (cancelled) return;
        if (me.role !== role) router.replace(`/${me.role}`);
        else setUser(me);
      })
      .catch(() => {
        if (!cancelled) router.replace("/login");
      });
    return () => {
      cancelled = true;
    };
  }, [role, router]);

  return user;
}
