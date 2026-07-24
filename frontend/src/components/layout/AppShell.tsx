"use client";

import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChannelSwitcher } from "@/components/layout/ChannelSwitcher";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { UserMenu } from "@/components/layout/UserMenu";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-[--color-border] px-6 py-3 dark:border-[--color-border-dark]">
          <ChannelSwitcher />
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <UserMenu />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
