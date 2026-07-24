"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md";

const variantClasses: Record<Variant, string> = {
  primary: "bg-[--color-accent] text-white hover:opacity-90 dark:bg-[--color-accent-dark]",
  secondary:
    "bg-[--color-surface] text-[--color-text] border border-[--color-border] hover:bg-[--color-border]/40 dark:bg-[--color-surface-dark] dark:text-[--color-text-dark] dark:border-[--color-border-dark]",
  danger: "bg-[--color-danger] text-white hover:opacity-90 dark:bg-[--color-danger-dark]",
  ghost: "bg-transparent hover:bg-[--color-surface] dark:hover:bg-[--color-surface-dark]",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-2.5 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {isLoading ? "…" : children}
    </button>
  ),
);
Button.displayName = "Button";
