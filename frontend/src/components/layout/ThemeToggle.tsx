"use client";

import { useThemeStore } from "@/lib/stores/theme-store";
import { IconSun, IconMoon } from "@/components/ui/icons";

export function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore();
  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="flex h-[34px] w-[34px] items-center justify-center rounded-lg border border-(--color-border) text-(--color-text-muted) transition-colors hover:bg-(--color-surface-2) hover:text-(--color-text) dark:border-(--color-border-dark) dark:text-(--color-text-muted-dark) dark:hover:bg-(--color-surface-2-dark) dark:hover:text-(--color-text-dark)"
    >
      {theme === "dark" ? <IconSun className="h-4 w-4" /> : <IconMoon className="h-4 w-4" />}
    </button>
  );
}
