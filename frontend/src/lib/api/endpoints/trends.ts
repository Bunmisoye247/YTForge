import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import { trendReadSchema, type TrendCreateRequest, type TrendRead } from "@/lib/api/schemas/trends";

const trendPageSchema = pageResponseSchema(trendReadSchema);

export function recordTrend(channelId: string, data: TrendCreateRequest): Promise<TrendRead> {
  return apiClient.post(`/channels/${channelId}/trends`, trendReadSchema, data);
}

export function listTrends(channelId: string, params?: PageParams): Promise<PageResponse<TrendRead>> {
  return apiClient.get(`/channels/${channelId}/trends`, trendPageSchema, pageParamsToSearch(params));
}
