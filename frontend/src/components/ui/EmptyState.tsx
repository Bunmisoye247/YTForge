import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type EmptyStateProps = {
  icon: ReactNode;
  title: string;
  description: ReactNode;
  action?: ReactNode;
  /** Tints the glyph amber instead of neutral — use when the page is
   * waiting on an upstream step rather than simply having nothing yet. */
  blocked?: boolean;
  /** Breadcrumb-style trail showing where the project sits in the
   * pipeline, e.g. "Idea ✓ → Script (in progress) → Storyboard". */
  trail?: ReactNode;
  className?: string;
};

export function EmptyState({ icon, title, description, action, blocked, trail, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-1.5 rounded-xl border-[1.5px] border-dashed border-(--color-border) px-6 py-14 text-center dark:border-(--color-border-dark)",
        className,
      )}
    >
      <div
        className={cn(
          "mb-2 flex h-[52px] w-[52px] items-center justify-center rounded-2xl [&>svg]:h-6 [&>svg]:w-6",
          blocked
            ? "bg-(--color-accent)/12 text-(--color-accent) dark:bg-(--color-accent-dark)/15 dark:text-(--color-accent-dark)"
            : "bg-(--color-surface-2) text-(--color-text-muted) dark:bg-(--color-surface-2-dark) dark:text-(--color-text-muted-dark)",
        )}
      >
        {icon}
      </div>
      <h3 className="font-display text-base font-semibold text-(--color-text) dark:text-(--color-text-dark)">{title}</h3>
      <p className="max-w-sm text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">{description}</p>
      {trail && (
        <div className="mt-1 flex items-center gap-2 font-mono text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
          {trail}
        </div>
      )}
      {action && <div className="mt-3.5">{action}</div>}
    </div>
  );
}

/** Bolded step name for use inside an EmptyState's `trail`, matching the
 * mockup's amber "current step" emphasis in the breadcrumb. */
export function TrailStep({ current, children }: { current?: boolean; children: ReactNode }) {
  return (
    <span className={current ? "font-medium text-(--color-accent) dark:text-(--color-accent-dark)" : undefined}>
      {children}
    </span>
  );
}
