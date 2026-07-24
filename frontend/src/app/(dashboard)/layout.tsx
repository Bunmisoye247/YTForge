"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/use-auth";
import { AppShell } from "@/components/layout/AppShell";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, isHydrating } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isHydrating && !isAuthenticated) router.replace("/login");
  }, [isHydrating, isAuthenticated, router]);

  if (isHydrating) {
    return <div className="flex h-screen items-center justify-center text-sm text-[--color-text-muted]">Loading…</div>;
  }
  if (!isAuthenticated) return null;

  return <AppShell>{children}</AppShell>;
}
