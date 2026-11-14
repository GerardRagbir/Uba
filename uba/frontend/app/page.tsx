"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Loading } from "@/components/Shell";
import { api, type User } from "@/lib/api";

// The front door: send each visitor to the right page for who they are.
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    api<User>("/auth/me")
      .then((user) => router.replace(`/${user.role}`))
      .catch(() => router.replace("/login"));
  }, [router]);

  return <Loading />;
}
