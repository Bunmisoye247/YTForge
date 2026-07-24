"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as storyboardsApi from "@/lib/api/endpoints/storyboards";
import type { SceneCreateRequest, StoryboardStatusUpdateRequest } from "@/lib/api/schemas/storyboards";
import { queryKeys } from "@/lib/api/query-keys";

export function useStoryboard(projectId: string) {
  return useQuery({
    queryKey: queryKeys.storyboards.detail(projectId),
    queryFn: () => storyboardsApi.getStoryboardForProject(projectId),
    enabled: Boolean(projectId),
  });
}

export function useCreateStoryboard(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scriptId: string) => storyboardsApi.createStoryboard(projectId, { script_id: scriptId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.storyboards.detail(projectId) }),
  });
}

export function useUpdateStoryboardStatus(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ storyboardId, data }: { storyboardId: string; data: StoryboardStatusUpdateRequest }) =>
      storyboardsApi.updateStoryboardStatus(storyboardId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.storyboards.detail(projectId) }),
  });
}

export function useScenes(storyboardId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.storyboards.scenes(storyboardId ?? ""),
    queryFn: () => storyboardsApi.listScenes(storyboardId as string),
    enabled: Boolean(storyboardId),
  });
}

export function useAddScene(storyboardId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SceneCreateRequest) => storyboardsApi.addScene(storyboardId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.storyboards.scenes(storyboardId) }),
  });
}

export function useReorderScenes(storyboardId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (orderedSceneIds: string[]) => storyboardsApi.reorderScenes(storyboardId, orderedSceneIds),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.storyboards.scenes(storyboardId) }),
  });
}
