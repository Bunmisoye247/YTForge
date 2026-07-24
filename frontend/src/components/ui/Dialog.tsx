"use client";

import { useEffect, type ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type DialogProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
};

export function Dialog({ open, onClose, title, children, className }: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <button
        aria-label="Close dialog"
        className="absolute inset-0 cursor-default"
        onClick={onClose}
        tabIndex={-1}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "relative z-10 w-full max-w-lg rounded-lg border border-[--color-border] bg-[--color-bg] p-5 shadow-xl dark:border-[--color-border-dark] dark:bg-[--color-surface-dark]",
          className,
        )}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[--color-text] dark:text-[--color-text-dark]">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-[--color-text-muted] hover:text-[--color-text] dark:text-[--color-text-muted-dark] dark:hover:text-[--color-text-dark]"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
