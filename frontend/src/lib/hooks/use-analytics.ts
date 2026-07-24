"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as analyticsApi from "@/lib/api/endpoints/analytics";
import type {
  DailyMetricIngestRequest,
  RetentionPointIngestRequest,
  TrafficSourceIngestRequest,
} from "@/lib/api/schemas/analytics";
import { queryKeys } from "@/lib/api/query-keys";

export function useVideoAnalytics(videoId: string) {
  return useQuery({
    queryKey: queryKeys.videos.analytics(videoId),
    queryFn: () => analyticsApi.getVideoAnalytics(videoId),
    enabled: Boolean(videoId),
  });
}

export function useIngestDailyMetric(videoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DailyMetricIngestRequest) => analyticsApi.ingestDailyMetric(videoId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.videos.analytics(videoId) }),
  });
}

export function useIngestRetentionPoint(videoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RetentionPointIngestRequest) => analyticsApi.ingestRetentionPoint(videoId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.videos.analytics(videoId) }),
  });
}

export function useIngestTrafficSource(videoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TrafficSourceIngestRequest) => analyticsApi.ingestTrafficSource(videoId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.videos.analytics(videoId) }),
  });
}
