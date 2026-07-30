"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useVideos } from "@/lib/hooks/use-videos";
import { useIngestDailyMetric, useVideoAnalytics } from "@/lib/hooks/use-analytics";
import { useToast } from "@/lib/stores/toast-store";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RetentionCurveChart } from "@/components/charts/RetentionCurveChart";
import { DailyMetricsChart } from "@/components/charts/DailyMetricsChart";
import { TrafficSourcesChart } from "@/components/charts/TrafficSourcesChart";

export default function AnalyticsPage() {
  const { projectId } = useSelectionStore();
  const { data: videoPage } = useVideos(projectId ?? "");
  const [videoId, setVideoId] = useState("");
  const { data: analytics, isLoading } = useVideoAnalytics(videoId);
  const ingestDaily = useIngestDailyMetric(videoId);
  const toast = useToast();

  const [open, setOpen] = useState(false);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [views, setViews] = useState("0");

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Analytics</h1>

      {!projectId ? (
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Select a project.</p>
      ) : (
        <Select value={videoId} onChange={(e) => setVideoId(e.target.value)} className="max-w-72" aria-label="Select video">
          <option value="">Select a video…</option>
          {videoPage?.items.map((v) => (
            <option key={v.id} value={v.id}>
              {v.title}
            </option>
          ))}
        </Select>
      )}

      {videoId && (
        <>
          <div className="flex justify-end">
            <Button size="sm" onClick={() => setOpen(true)}>
              Ingest daily metric
            </Button>
          </div>

          {isLoading ? (
            <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Loading…</p>
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Daily metrics</CardTitle>
                </CardHeader>
                <DailyMetricsChart metrics={analytics?.daily_metrics ?? []} />
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Audience retention</CardTitle>
                </CardHeader>
                <RetentionCurveChart points={analytics?.retention_points ?? []} />
              </Card>
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Traffic sources</CardTitle>
                </CardHeader>
                <TrafficSourcesChart sources={analytics?.traffic_sources ?? []} />
              </Card>
            </div>
          )}
        </>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="Ingest daily metric">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="metric-date">Date</Label>
            <Input id="metric-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="metric-views">Views</Label>
            <Input id="metric-views" type="number" min={0} value={views} onChange={(e) => setViews(e.target.value)} />
          </div>
          <div className="flex justify-end">
            <Button
              isLoading={ingestDaily.isPending}
              onClick={() =>
                ingestDaily.mutate(
                  { date, views: Number(views) },
                  {
                    onSuccess: () => {
                      toast.success("Metric ingested");
                      setOpen(false);
                    },
                    onError: () => toast.error("Failed to ingest metric"),
                  },
                )
              }
            >
              Ingest
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
