"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as trendsApi from "@/lib/api/endpoints/trends";
import type { TrendCreateRequest } from "@/lib/api/schemas/trends";
import type { PageParams } from "@/lib/api/schemas/pagination";
import { queryKeys } from "@/lib/api/query-keys";

export function useTrends(channelId: string, params?: PageParams) {
  return useQuery({
    queryKey: [...queryKeys.trends.list(channelId), params],
    queryFn: () => trendsApi.listTrends(channelId, params),
    enabled: Boolean(channelId),
  });
}

export function useRecordTrend(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TrendCreateRequest) => trendsApi.recordTrend(channelId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.trends.list(channelId) }),
  });
}
