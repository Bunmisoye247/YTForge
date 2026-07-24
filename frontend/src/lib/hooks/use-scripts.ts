"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as scriptsApi from "@/lib/api/endpoints/scripts";
import type {
  FactCheckCreateRequest,
  ScriptCreateRequest,
  ScriptStatusUpdateRequest,
} from "@/lib/api/schemas/scripts";
import { queryKeys } from "@/lib/api/query-keys";

export function useScripts(projectId: string) {
  return useQuery({
    queryKey: queryKeys.scripts.list(projectId),
    queryFn: () => scriptsApi.listScripts(projectId),
    enabled: Boolean(projectId),
  });
}

export function useCreateScriptVersion(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ScriptCreateRequest) => scriptsApi.createScriptVersion(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.scripts.list(projectId) }),
  });
}

export function useUpdateScriptStatus(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scriptId, data }: { scriptId: string; data: ScriptStatusUpdateRequest }) =>
      scriptsApi.updateScriptStatus(scriptId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.scripts.list(projectId) }),
  });
}

export function useFactChecks(scriptId: string) {
  return useQuery({
    queryKey: queryKeys.scripts.factChecks(scriptId),
    queryFn: () => scriptsApi.listFactChecks(scriptId),
    enabled: Boolean(scriptId),
  });
}

export function useAddFactCheck(scriptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FactCheckCreateRequest) => scriptsApi.addFactCheck(scriptId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.scripts.factChecks(scriptId) }),
  });
}
