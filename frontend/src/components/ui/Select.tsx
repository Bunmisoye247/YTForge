"use client";

import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "w-full rounded-md border border-[--color-border] bg-[--color-bg] px-3 py-2 text-sm text-[--color-text] outline-none focus:border-[--color-accent] dark:border-[--color-border-dark] dark:bg-[--color-bg-dark] dark:text-[--color-text-dark]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
);
Select.displayName = "Select";
