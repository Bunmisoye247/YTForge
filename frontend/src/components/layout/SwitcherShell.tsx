import type { ReactNode } from "react";

/** Shared pill container for the topbar's Channel/Project switchers —
 * a labeled box wrapping a `<Select bare>`. */
export function SwitcherShell({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-(--color-border) bg-(--color-surface-2) px-3 py-1.5 dark:border-(--color-border-dark) dark:bg-(--color-surface-2-dark)">
      <span className="font-mono text-[10px] font-medium tracking-widest text-(--color-text-muted) uppercase dark:text-(--color-text-muted-dark)">
        {label}
      </span>
      {children}
    </div>
  );
}
