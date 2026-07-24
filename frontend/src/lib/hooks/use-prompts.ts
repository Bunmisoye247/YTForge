"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as promptsApi from "@/lib/api/endpoints/prompts";
import type { PromptVersionCreateRequest } from "@/lib/api/schemas/prompts";
import { queryKeys } from "@/lib/api/query-keys";

export function usePromptTemplates() {
  return useQuery({
    queryKey: queryKeys.prompts.templates,
    queryFn: promptsApi.listPromptTemplates,
  });
}

export function usePromptVersions(templateId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.prompts.versions(templateId ?? ""),
    queryFn: () => promptsApi.listPromptVersions(templateId as string),
    enabled: Boolean(templateId),
  });
}

export function useCreatePromptVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PromptVersionCreateRequest) => promptsApi.createPromptVersion(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.prompts.templates }),
  });
}
