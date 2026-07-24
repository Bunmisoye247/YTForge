import { z } from "zod";

export const dailyMetricReadSchema = z.object({
  id: z.string().uuid(),
  video_id: z.string().uuid(),
  date: z.string(),
  views: z.number(),
  watch_time_minutes: z.string(),
  likes: z.number(),
  comments: z.number(),
  shares: z.number(),
  subscribers_gained: z.number(),
  revenue_usd: z.string(),
});
export type DailyMetricRead = z.infer<typeof dailyMetricReadSchema>;

export const retentionPointReadSchema = z.object({
  id: z.string().uuid(),
  video_id: z.string().uuid(),
  date: z.string(),
  elapsed_video_percent: z.string(),
  audience_retention_percent: z.string(),
});
export type RetentionPointRead = z.infer<typeof retentionPointReadSchema>;

export const trafficSourceReadSchema = z.object({
  id: z.string().uuid(),
  video_id: z.string().uuid(),
  date: z.string(),
  source_type: z.string(),
  views: z.number(),
  watch_time_minutes: z.string(),
});
export type TrafficSourceRead = z.infer<typeof trafficSourceReadSchema>;

export const videoAnalyticsReadSchema = z.object({
  daily_metrics: z.array(dailyMetricReadSchema),
  retention_points: z.array(retentionPointReadSchema),
  traffic_sources: z.array(trafficSourceReadSchema),
});
export type VideoAnalyticsRead = z.infer<typeof videoAnalyticsReadSchema>;

export type DailyMetricIngestRequest = {
  date: string;
  views?: number;
  watch_time_minutes?: string;
  likes?: number;
  comments?: number;
  shares?: number;
  subscribers_gained?: number;
  revenue_usd?: string;
};

export type RetentionPointIngestRequest = {
  date: string;
  elapsed_video_percent: string;
  audience_retention_percent: string;
};

export type TrafficSourceIngestRequest = {
  date: string;
  source_type: string;
  views?: number;
  watch_time_minutes?: string;
};
