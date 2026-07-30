"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";
import { useMyChannels } from "@/lib/hooks/use-channels";
import { useProjects } from "@/lib/hooks/use-projects";
import { useApprovals } from "@/lib/hooks/use-approvals";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { ApprovalStatus } from "@/types/enums";
import {
  IconOverview,
  IconChannels,
  IconProjects,
  IconIdeas,
  IconScripts,
  IconStoryboards,
  IconImages,
  IconVideos,
  IconUploads,
  IconAnalytics,
  IconApprovals,
  IconSettings,
} from "@/components/ui/icons";

type NavItem = { href: string; label: string; icon: (props: { className?: string }) => ReactNode; count?: number };

function useNavGroups(): { label: string; items: NavItem[] }[] {
  const { channelId } = useSelectionStore();
  const { data: channels } = useMyChannels();
  const { data: projectPage } = useProjects(channelId ?? "", { limit: 1 });
  const { data: pendingApprovals } = useApprovals(ApprovalStatus.PENDING, { limit: 1 });

  return [
    {
      label: "Workspace",
      items: [
        { href: "/overview", label: "Overview", icon: IconOverview },
        { href: "/channels", label: "Channels", icon: IconChannels, count: channels?.length },
        { href: "/projects", label: "Projects", icon: IconProjects, count: projectPage?.total },
      ],
    },
    {
      label: "Pipeline",
      items: [
        { href: "/ideas", label: "Ideas", icon: IconIdeas },
        { href: "/scripts", label: "Scripts", icon: IconScripts },
        { href: "/storyboards", label: "Storyboards", icon: IconStoryboards },
        { href: "/images", label: "Images", icon: IconImages },
        { href: "/videos", label: "Videos", icon: IconVideos },
        { href: "/uploads", label: "Uploads", icon: IconUploads },
      ],
    },
    {
      label: "Manage",
      items: [
        { href: "/analytics", label: "Analytics", icon: IconAnalytics },
        { href: "/approvals", label: "Approvals", icon: IconApprovals, count: pendingApprovals?.total },
        { href: "/settings", label: "Settings", icon: IconSettings },
      ],
    },
  ];
}

export function Sidebar() {
  const pathname = usePathname();
  const groups = useNavGroups();

  return (
    <nav className="flex h-full w-60 shrink-0 flex-col gap-1 border-r border-(--color-border) bg-(--color-surface) p-3 dark:border-(--color-border-dark) dark:bg-(--color-surface-dark)">
      <div className="mb-2 flex items-center gap-2.5 px-2 pb-3 pt-1">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-(--color-accent) to-(--color-danger) text-sm text-(--color-accent-ink) shadow-[0_0_14px_-4px_var(--color-accent)] dark:from-(--color-accent-dark) dark:to-[#c86f1e] dark:shadow-[0_0_14px_-4px_var(--color-accent-dark)]">
          ⚒
        </span>
        <span className="font-display text-lg font-bold tracking-tight text-(--color-text) dark:text-(--color-text-dark)">
          YTForge
        </span>
      </div>

      {groups.map((group) => (
        <div key={group.label} className="mt-2 first:mt-0">
          <div className="px-3 pb-1.5 font-mono text-[10.5px] font-medium tracking-widest text-(--color-text-muted) uppercase dark:text-(--color-text-muted-dark)">
            {group.label}
          </div>
          {group.items.map((item) => {
            const active = pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-(--color-accent)/12 text-(--color-accent) dark:bg-(--color-accent-dark)/15 dark:text-(--color-accent-dark)"
                    : "text-(--color-text-muted) hover:bg-(--color-surface-2) hover:text-(--color-text) dark:text-(--color-text-muted-dark) dark:hover:bg-(--color-surface-2-dark) dark:hover:text-(--color-text-dark)",
                )}
              >
                {active && (
                  <span className="absolute inset-y-2 left-0 w-[3px] rounded-r bg-(--color-accent) dark:bg-(--color-accent-dark)" />
                )}
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
                {typeof item.count === "number" && (
                  <span
                    className={cn(
                      "ml-auto rounded-full px-1.5 py-0.5 font-mono text-[11px]",
                      active
                        ? "bg-(--color-accent)/18 text-(--color-accent) dark:bg-(--color-accent-dark)/20 dark:text-(--color-accent-dark)"
                        : "bg-(--color-surface-2) text-(--color-text-muted) dark:bg-(--color-surface-2-dark) dark:text-(--color-text-muted-dark)",
                    )}
                  >
                    {item.count}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      ))}
      <div className="flex-1" />
    </nav>
  );
}
