import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import { approvalReadSchema, type ApprovalRead } from "@/lib/api/schemas/approvals";
import {
  assetReadSchema,
  presignedUrlReadSchema,
  type AssetRead,
  type AssetRegisterRequest,
} from "@/lib/api/schemas/assets";

const assetPageSchema = pageResponseSchema(assetReadSchema);

export function registerAsset(projectId: string, data: AssetRegisterRequest): Promise<AssetRead> {
  return apiClient.post(`/projects/${projectId}/assets`, assetReadSchema, data);
}

export function listAssets(projectId: string, params?: PageParams): Promise<PageResponse<AssetRead>> {
  return apiClient.get(`/projects/${projectId}/assets`, assetPageSchema, pageParamsToSearch(params));
}

export function markAssetReady(assetId: string): Promise<AssetRead> {
  return apiClient.post(`/assets/${assetId}/ready`, assetReadSchema);
}

export function markAssetFailed(assetId: string): Promise<AssetRead> {
  return apiClient.post(`/assets/${assetId}/failed`, assetReadSchema);
}

export function requestAssetDeletion(assetId: string): Promise<ApprovalRead> {
  return apiClient.post(`/assets/${assetId}/request-deletion`, approvalReadSchema);
}

export function getAssetPresignedUrl(assetId: string): Promise<{ url: string }> {
  return apiClient.get(`/assets/${assetId}/presigned-url`, presignedUrlReadSchema);
}
