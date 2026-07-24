"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as assetsApi from "@/lib/api/endpoints/assets";
import type { AssetRegisterRequest } from "@/lib/api/schemas/assets";
import type { PageParams } from "@/lib/api/schemas/pagination";
import { queryKeys } from "@/lib/api/query-keys";

export function useAssets(projectId: string, params?: PageParams) {
  return useQuery({
    queryKey: [...queryKeys.assets.list(projectId), params],
    queryFn: () => assetsApi.listAssets(projectId, params),
    enabled: Boolean(projectId),
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
