import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-lg border border-[--color-border] bg-[--color-bg] p-4 dark:border-[--color-border-dark] dark:bg-[--color-surface-dark]",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mb-3 flex items-center justify-between", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-sm font-semibold text-[--color-text-muted] dark:text-[--color-text-muted-dark]", className)} {...props} />;
}
