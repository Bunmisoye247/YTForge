"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as videosApi from "@/lib/api/endpoints/videos";
import type { SeoMetadataSetRequest, VideoCreateRequest, VideoUpdateRequest } from "@/lib/api/schemas/videos";
import type { PageParams } from "@/lib/api/schemas/pagination";
import { queryKeys } from "@/lib/api/query-keys";

export function useVideos(projectId: string, params?: PageParams) {
  return useQuery({
    queryKey: [...queryKeys.videos.list(projectId), params],
    queryFn: () => videosApi.listVideos(projectId, params),
    enabled: Boolean(projectId),
  });
}

export function useCreateVideo(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VideoCreateRequest) => videosApi.createVideo(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.videos.list(projectId) }),
  });
}

export function useUpdateVideo(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ videoId, data }: { videoId: string; data: VideoUpdateRequest }) =>
      videosApi.updateVideo(videoId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.videos.list(projectId) }),
  });
}

export function useRequestPublishApproval() {
  return useMutation({
    mutationFn: (videoId: string) => videosApi.requestPublishApproval(videoId),
  });
}

export function useSeoMetadata(videoId: string) {
  return useQuery({
    queryKey: queryKeys.videos.seo(videoId),
    queryFn: () => videosApi.getSeoMetadata(videoId),
    enabled: Boolean(videoId),
  });
}

export function useSetSeoMetadata(videoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SeoMetadataSetRequest) => videosApi.setSeoMetadata(videoId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.videos.seo(videoId) }),
  });
}
