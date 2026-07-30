"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useChartMode } from "@/components/charts/use-chart-mode";
import type { RetentionPointRead } from "@/lib/api/schemas/analytics";

export function RetentionCurveChart({ points }: { points: RetentionPointRead[] }) {
  const { colors } = useChartMode();

  if (points.length === 0) {
    return (
      <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
        No retention data yet.
      </p>
    );
  }

  const data = [...points]
    .sort((a, b) => Number(a.elapsed_video_percent) - Number(b.elapsed_video_percent))
    .map((p) => ({
      elapsed: Number(p.elapsed_video_percent),
      retention: Number(p.audience_retention_percent),
    }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={colors.gridline} strokeDasharray="0" vertical={false} />
        <XAxis
          dataKey="elapsed"
          tickFormatter={(v: number) => `${v}%`}
          stroke={colors.baseline}
          tick={{ fill: colors.mutedInk, fontSize: 12 }}
          axisLine={{ stroke: colors.baseline }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tickFormatter={(v: number) => `${v}%`}
          stroke={colors.baseline}
          tick={{ fill: colors.mutedInk, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip
          formatter={(value: number) => [`${value}%`, "Retention"]}
          labelFormatter={(label: number) => `${label}% elapsed`}
          contentStyle={{ background: colors.surface, border: `1px solid ${colors.gridline}`, fontSize: 12 }}
        />
        <Line
          type="monotone"
          dataKey="retention"
          stroke={colors.series1}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, strokeWidth: 2, stroke: colors.surface }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
