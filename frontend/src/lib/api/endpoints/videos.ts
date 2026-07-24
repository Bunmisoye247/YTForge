import { apiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import { approvalReadSchema, type ApprovalRead } from "@/lib/api/schemas/approvals";
import {
  seoMetadataReadSchema,
  videoReadSchema,
  type SeoMetadataRead,
  type SeoMetadataSetRequest,
  type VideoCreateRequest,
  type VideoRead,
  type VideoUpdateRequest,
} from "@/lib/api/schemas/videos";

const videoPageSchema = pageResponseSchema(videoReadSchema);

export function createVideo(projectId: string, data: VideoCreateRequest): Promise<VideoRead> {
  return apiClient.post(`/projects/${projectId}/videos`, videoReadSchema, data);
}

export function listVideos(projectId: string, params?: PageParams): Promise<PageResponse<VideoRead>> {
  return apiClient.get(`/projects/${projectId}/videos`, videoPageSchema, pageParamsToSearch(params));
}

export function updateVideo(videoId: string, data: VideoUpdateRequest): Promise<VideoRead> {
  return apiClient.patch(`/videos/${videoId}`, videoReadSchema, data);
}

export function requestPublishApproval(videoId: string): Promise<ApprovalRead> {
  return apiClient.post(`/videos/${videoId}/request-publish-approval`, approvalReadSchema);
}

export function setSeoMetadata(videoId: string, data: SeoMetadataSetRequest): Promise<SeoMetadataRead> {
  return apiClient.put(`/videos/${videoId}/seo`, seoMetadataReadSchema, data);
}

/** Returns null if no SEO metadata has been set for this video yet. */
export async function getSeoMetadata(videoId: string): Promise<SeoMetadataRead | null> {
  try {
    return await apiClient.get(`/videos/${videoId}/seo`, seoMetadataReadSchema);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
