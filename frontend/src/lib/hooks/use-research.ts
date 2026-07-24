"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as researchApi from "@/lib/api/endpoints/research";
import type { ResearchDocumentCreateRequest } from "@/lib/api/schemas/research";
import { queryKeys } from "@/lib/api/query-keys";

export function useResearchDocuments(projectId: string) {
  return useQuery({
    queryKey: queryKeys.research.list(projectId),
    queryFn: () => researchApi.listResearchDocuments(projectId),
    enabled: Boolean(projectId),
  });
}

export function useAddResearchDocument(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ResearchDocumentCreateRequest) => researchApi.addResearchDocument(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.research.list(projectId) }),
  });
}
