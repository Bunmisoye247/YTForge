"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as approvalsApi from "@/lib/api/endpoints/approvals";
import type { ApprovalDecisionRequest, ApprovalRequestRequest } from "@/lib/api/schemas/approvals";
import type { PageParams } from "@/lib/api/schemas/pagination";
import type { ApprovalStatus } from "@/types/enums";
import { queryKeys } from "@/lib/api/query-keys";

export function useApprovals(status?: ApprovalStatus, params?: PageParams) {
  return useQuery({
    queryKey: [...queryKeys.approvals.list(status), params],
    queryFn: () => approvalsApi.listApprovals({ ...params, status_filter: status }),
  });
}

export function useRequestApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ApprovalRequestRequest) => approvalsApi.requestApproval(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvals"] }),
  });
}

export function useDecideApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ approvalId, data }: { approvalId: string; data: ApprovalDecisionRequest }) =>
      approvalsApi.decideApproval(approvalId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvals"] }),
  });
}
