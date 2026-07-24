import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import {
  projectReadSchema,
  type ProjectCreateRequest,
  type ProjectRead,
  type ProjectStatusUpdateRequest,
  type ProjectUpdateRequest,
} from "@/lib/api/schemas/projects";

const projectPageSchema = pageResponseSchema(projectReadSchema);

export function createProject(channelId: string, data: ProjectCreateRequest): Promise<ProjectRead> {
  return apiClient.post(`/channels/${channelId}/projects`, projectReadSchema, data);
}

export function listProjects(
  channelId: string,
  params?: PageParams,
): Promise<PageResponse<ProjectRead>> {
  return apiClient.get(`/channels/${channelId}/projects`, projectPageSchema, pageParamsToSearch(params));
}

export function updateProject(projectId: string, data: ProjectUpdateRequest): Promise<ProjectRead> {
  return apiClient.patch(`/projects/${projectId}`, projectReadSchema, data);
}

export function updateProjectStatus(
  projectId: string,
  data: ProjectStatusUpdateRequest,
): Promise<ProjectRead> {
  return apiClient.post(`/projects/${projectId}/status`, projectReadSchema, data);
}
