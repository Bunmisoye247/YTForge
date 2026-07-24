"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useChartMode } from "@/components/charts/use-chart-mode";
import { titleCase } from "@/lib/utils/format";
import type { TrafficSourceRead } from "@/lib/api/schemas/analytics";

/** One bar per source, aggregated across the ingested dates. Identity here
 * is carried by the axis labels (source names), not per-bar hue — so every
 * bar uses the same series color, per the skill's "color follows the
 * entity" rule (these bars are one entity — views — sliced by category,
 * not distinct series). */
export function TrafficSourcesChart({ sources }: { sources: TrafficSourceRead[] }) {
  const { colors } = useChartMode();

  if (sources.length === 0) {
    return (
      <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
        No traffic source data yet.
      </p>
    );
  }

  const totals = new Map<string, number>();
  for (const s of sources) {
    totals.set(s.source_type, (totals.get(s.source_type) ?? 0) + s.views);
  }
  const data = [...totals.entries()]
    .map(([source, views]) => ({ source: titleCase(source), views }))
    .sort((a, b) => b.views - a.views);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.gridline} strokeDasharray="0" vertical={false} />
        <XAxis
          dataKey="source"
          stroke={colors.baseline}
          tick={{ fill: colors.mutedInk, fontSize: 12 }}
          axisLine={{ stroke: colors.baseline }}
          tickLine={false}
        />
        <YAxis
          stroke={colors.baseline}
          tick={{ fill: colors.mutedInk, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip
          formatter={(value: number) => [value.toLocaleString(), "Views"]}
          contentStyle={{ background: colors.surface, border: `1px solid ${colors.gridline}`, fontSize: 12 }}
        />
        <Bar dataKey="views" fill={colors.series1} radius={[4, 4, 0, 0]} maxBarSize={24} />
      </BarChart>
    </ResponsiveContainer>
  );
}
