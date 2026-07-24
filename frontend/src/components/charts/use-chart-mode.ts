"use client";

import { useThemeStore } from "@/lib/stores/theme-store";
import { chartColors, type ChartMode } from "@/components/charts/chart-theme";

export function useChartMode(): { mode: ChartMode; colors: (typeof chartColors)[ChartMode] } {
  const theme = useThemeStore((s) => s.theme);
  return { mode: theme, colors: chartColors[theme] };
}
