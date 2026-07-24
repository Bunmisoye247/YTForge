"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as modelsApi from "@/lib/api/endpoints/models";
import type { ModelRegisterRequest, ModelStatusUpdateRequest } from "@/lib/api/schemas/models";
import { queryKeys } from "@/lib/api/query-keys";

export function useModels() {
  return useQuery({
    queryKey: queryKeys.models.list,
    queryFn: modelsApi.listModels,
  });
}

export function useRegisterModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ModelRegisterRequest) => modelsApi.registerModel(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.models.list }),
  });
}

export function useUpdateModelStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, data }: { entryId: string; data: ModelStatusUpdateRequest }) =>
      modelsApi.updateModelStatus(entryId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.models.list }),
  });
}
