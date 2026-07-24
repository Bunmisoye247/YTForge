import { apiClient } from "@/lib/api/client";
import {
  dailyMetricReadSchema,
  retentionPointReadSchema,
  trafficSourceReadSchema,
  videoAnalyticsReadSchema,
  type DailyMetricIngestRequest,
  type DailyMetricRead,
  type RetentionPointIngestRequest,
  type RetentionPointRead,
  type TrafficSourceIngestRequest,
  type TrafficSourceRead,
  type VideoAnalyticsRead,
} from "@/lib/api/schemas/analytics";

export function getVideoAnalytics(videoId: string): Promise<VideoAnalyticsRead> {
  return apiClient.get(`/videos/${videoId}/analytics`, videoAnalyticsReadSchema);
}

export function ingestDailyMetric(
  videoId: string,
  data: DailyMetricIngestRequest,
): Promise<DailyMetricRead> {
  return apiClient.post(`/videos/${videoId}/analytics/daily-metrics`, dailyMetricReadSchema, data);
}

export function ingestRetentionPoint(
  videoId: string,
  data: RetentionPointIngestRequest,
): Promise<RetentionPointRead> {
  return apiClient.post(`/videos/${videoId}/analytics/retention-points`, retentionPointReadSchema, data);
}

export function ingestTrafficSource(
  videoId: string,
  data: TrafficSourceIngestRequest,
): Promise<TrafficSourceRead> {
  return apiClient.post(`/videos/${videoId}/analytics/traffic-sources`, trafficSourceReadSchema, data);
}
