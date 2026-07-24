"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as projectsApi from "@/lib/api/endpoints/projects";
import type { ProjectCreateRequest, ProjectStatusUpdateRequest, ProjectUpdateRequest } from "@/lib/api/schemas/projects";
import type { PageParams } from "@/lib/api/schemas/pagination";
import { queryKeys } from "@/lib/api/query-keys";

export function useProjects(channelId: string, params?: PageParams) {
  return useQuery({
    queryKey: [...queryKeys.projects.list(channelId), params],
    queryFn: () => projectsApi.listProjects(channelId, params),
    enabled: Boolean(channelId),
  });
}

export function useCreateProject(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreateRequest) => projectsApi.createProject(channelId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects.list(channelId) }),
  });
}

export function useUpdateProject(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectUpdateRequest }) =>
      projectsApi.updateProject(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects.list(channelId) }),
  });
}

export function useUpdateProjectStatus(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectStatusUpdateRequest }) =>
      projectsApi.updateProjectStatus(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects.list(channelId) }),
  });
}
