"use client";

import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useChartMode } from "@/components/charts/use-chart-mode";
import { Select } from "@/components/ui/Select";
import { formatDate } from "@/lib/utils/format";
import type { DailyMetricRead } from "@/lib/api/schemas/analytics";

// Never plot two of these on one dual-axis chart (see dataviz skill's "one
// axis" rule) — a Select lets the viewer pick a single measure instead.
const METRICS = [
  { key: "views", label: "Views" },
  { key: "watch_time_minutes", label: "Watch time (minutes)" },
  { key: "likes", label: "Likes" },
  { key: "comments", label: "Comments" },
  { key: "shares", label: "Shares" },
  { key: "subscribers_gained", label: "Subscribers gained" },
  { key: "revenue_usd", label: "Revenue (USD)" },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

export function DailyMetricsChart({ metrics }: { metrics: DailyMetricRead[] }) {
  const { colors } = useChartMode();
  const [metric, setMetric] = useState<MetricKey>("views");

  if (metrics.length === 0) {
    return (
      <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
        No daily metrics ingested yet.
      </p>
    );
  }

  const data = [...metrics]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((m) => ({ date: m.date, value: Number(m[metric]) }));

  const label = METRICS.find((m) => m.key === metric)!.label;

  return (
    <div className="flex flex-col gap-2">
      <Select value={metric} onChange={(e) => setMetric(e.target.value as MetricKey)} className="max-w-56">
        {METRICS.map((m) => (
          <option key={m.key} value={m.key}>
            {m.label}
          </option>
        ))}
      </Select>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke={colors.gridline} strokeDasharray="0" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(v: string) => formatDate(v)}
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
            width={56}
          />
          <Tooltip
            formatter={(value: number) => [value.toLocaleString(), label]}
            labelFormatter={(v: string) => formatDate(v)}
            contentStyle={{ background: colors.surface, border: `1px solid ${colors.gridline}`, fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="value"
            name={label}
            stroke={colors.series1}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: colors.surface }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
