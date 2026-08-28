"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as assetsApi from "@/lib/api/endpoints/assets";
import type { AssetRegisterRequest, ImageGenerateRequest } from "@/lib/api/schemas/assets";
import type { PageParams } from "@/lib/api/schemas/pagination";
import { queryKeys } from "@/lib/api/query-keys";
import { usePipelineStatus } from "@/lib/hooks/use-pipeline-status";

/** Polls while a pipeline job is running for this project — see
 * useScripts. */
export function useAssets(projectId: string, params?: PageParams) {
  const { hasActiveJobs } = usePipelineStatus(projectId || undefined);
  return useQuery({
    queryKey: [...queryKeys.assets.list(projectId), params],
    queryFn: () => assetsApi.listAssets(projectId, params),
    enabled: Boolean(projectId),
    refetchInterval: hasActiveJobs ? 5_000 : false,
  });
}

export function useGenerateProjectImage(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ImageGenerateRequest) => assetsApi.generateProjectImage(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.assets.list(projectId) }),
  });
}

export function useAssetPresignedUrl(assetId: string | undefined) {
  return useQuery({
    queryKey: ["assets", "presigned-url", assetId ?? ""],
    queryFn: () => assetsApi.getAssetPresignedUrl(assetId as string),
    enabled: Boolean(assetId),
    // Presigned URLs expire (default 1h server-side) — treat as stale
    // quickly enough that a long-open tab doesn't hold a dead link, but
    // not so eagerly that every render re-fetches.
    staleTime: 15 * 60 * 1000,
  });
}

export function useRegisterAsset(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AssetRegisterRequest) => assetsApi.registerAsset(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.assets.list(projectId) }),
  });
}

export function useMarkAssetReady(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assetId: string) => assetsApi.markAssetReady(assetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.assets.list(projectId) }),
  });
}

export function useMarkAssetFailed(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assetId: string) => assetsApi.markAssetFailed(assetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.assets.list(projectId) }),
  });
}

export function useRequestAssetDeletion() {
  return useMutation({
    mutationFn: (assetId: string) => assetsApi.requestAssetDeletion(assetId),
  });
}
