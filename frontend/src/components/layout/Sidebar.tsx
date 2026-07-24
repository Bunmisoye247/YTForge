"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils/cn";

const NAV_ITEMS = [
  { href: "/overview", label: "Overview" },
  { href: "/channels", label: "Channels" },
  { href: "/projects", label: "Projects" },
  { href: "/ideas", label: "Ideas" },
  { href: "/scripts", label: "Scripts" },
  { href: "/storyboards", label: "Storyboards" },
  { href: "/images", label: "Images" },
  { href: "/videos", label: "Videos" },
  { href: "/uploads", label: "Uploads" },
  { href: "/analytics", label: "Analytics" },
  { href: "/approvals", label: "Approvals" },
  { href: "/settings", label: "Settings" },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex h-full w-56 shrink-0 flex-col gap-1 border-r border-[--color-border] p-3 dark:border-[--color-border-dark]">
      <div className="mb-3 px-2 text-lg font-semibold text-[--color-text] dark:text-[--color-text-dark]">
        YTForge
      </div>
      {NAV_ITEMS.map((item) => {
        const active = pathname?.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-[--color-accent] text-white"
                : "text-[--color-text-muted] hover:bg-[--color-surface] dark:text-[--color-text-muted-dark] dark:hover:bg-[--color-surface-dark]",
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
