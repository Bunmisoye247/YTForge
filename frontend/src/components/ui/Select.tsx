"use client";

import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

const fieldClassName =
  "w-full rounded-lg border border-(--color-border) bg-(--color-bg) px-3 py-2 text-sm text-(--color-text) outline-none focus:border-(--color-accent) dark:border-(--color-border-dark) dark:bg-(--color-bg-dark) dark:text-(--color-text-dark)";

// Used inside SwitcherShell's own pill container, which already supplies
// the border/background — a plain className merge (this codebase's `cn`
// is a clsx wrapper, not tailwind-merge) can't reliably override the
// conflicting utilities in `fieldClassName`, so this is a distinct variant
// rather than an override.
const bareClassName = "w-auto max-w-40 border-0 bg-transparent p-0 text-sm font-semibold outline-none";

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & { bare?: boolean };

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, bare, children, ...props }, ref) => (
    <select ref={ref} className={cn(bare ? bareClassName : fieldClassName, className)} {...props}>
      {children}
    </select>
  ),
);
Select.displayName = "Select";
