import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import {
  factCheckReadSchema,
  scriptReadSchema,
  type FactCheckCreateRequest,
  type FactCheckRead,
  type ScriptCreateRequest,
  type ScriptRead,
  type ScriptStatusUpdateRequest,
} from "@/lib/api/schemas/scripts";
import { z } from "zod";

const scriptPageSchema = pageResponseSchema(scriptReadSchema);

export function createScriptVersion(projectId: string, data: ScriptCreateRequest): Promise<ScriptRead> {
  return apiClient.post(`/projects/${projectId}/scripts`, scriptReadSchema, data);
}

export function listScripts(projectId: string, params?: PageParams): Promise<PageResponse<ScriptRead>> {
  return apiClient.get(`/projects/${projectId}/scripts`, scriptPageSchema, pageParamsToSearch(params));
}

export function updateScriptStatus(
  scriptId: string,
  data: ScriptStatusUpdateRequest,
): Promise<ScriptRead> {
  return apiClient.post(`/scripts/${scriptId}/status`, scriptReadSchema, data);
}

export function addFactCheck(scriptId: string, data: FactCheckCreateRequest): Promise<FactCheckRead> {
  return apiClient.post(`/scripts/${scriptId}/fact-checks`, factCheckReadSchema, data);
}

export function listFactChecks(scriptId: string): Promise<FactCheckRead[]> {
  return apiClient.get(`/scripts/${scriptId}/fact-checks`, z.array(factCheckReadSchema));
}
