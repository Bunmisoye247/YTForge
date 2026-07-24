import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import {
  approvalReadSchema,
  type ApprovalDecisionRequest,
  type ApprovalRead,
  type ApprovalRequestRequest,
} from "@/lib/api/schemas/approvals";
import type { ApprovalStatus } from "@/types/enums";

const approvalPageSchema = pageResponseSchema(approvalReadSchema);

export function requestApproval(data: ApprovalRequestRequest): Promise<ApprovalRead> {
  return apiClient.post("/approvals", approvalReadSchema, data);
}

export function listApprovals(
  params?: PageParams & { status_filter?: ApprovalStatus },
): Promise<PageResponse<ApprovalRead>> {
  const search = pageParamsToSearch(params);
  if (params?.status_filter) search.set("status_filter", params.status_filter);
  return apiClient.get("/approvals", approvalPageSchema, search);
}

export function decideApproval(approvalId: string, data: ApprovalDecisionRequest): Promise<ApprovalRead> {
  return apiClient.post(`/approvals/${approvalId}/decision`, approvalReadSchema, data);
}
