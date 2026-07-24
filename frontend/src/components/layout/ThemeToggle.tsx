"use client";

import { useThemeStore } from "@/lib/stores/theme-store";
import { Button } from "@/components/ui/Button";

export function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore();
  return (
    <Button variant="ghost" size="sm" onClick={toggleTheme} aria-label="Toggle theme">
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </Button>
  );
}
