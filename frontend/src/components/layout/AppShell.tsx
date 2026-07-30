"use client";

import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChannelSwitcher } from "@/components/layout/ChannelSwitcher";
import { ProjectPicker } from "@/components/layout/ProjectPicker";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { UserMenu } from "@/components/layout/UserMenu";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen bg-(--color-bg) dark:bg-(--color-bg-dark)">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center gap-3 border-b border-(--color-border) bg-(--color-surface) px-7 py-3.5 dark:border-(--color-border-dark) dark:bg-(--color-surface-dark)">
          <ChannelSwitcher />
          <ProjectPicker />
          <div className="ml-auto flex items-center gap-3.5">
            <ThemeToggle />
            <UserMenu />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-7">{children}</main>
      </div>
    </div>
  );
}
