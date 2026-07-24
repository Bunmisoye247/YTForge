import { apiClient } from "@/lib/api/client";
import {
  modelRegistryEntryReadSchema,
  type ModelRegisterRequest,
  type ModelRegistryEntryRead,
  type ModelStatusUpdateRequest,
} from "@/lib/api/schemas/models";
import { z } from "zod";

export function registerModel(data: ModelRegisterRequest): Promise<ModelRegistryEntryRead> {
  return apiClient.post("/models", modelRegistryEntryReadSchema, data);
}

export function listModels(): Promise<ModelRegistryEntryRead[]> {
  return apiClient.get("/models", z.array(modelRegistryEntryReadSchema));
}

export function updateModelStatus(
  entryId: string,
  data: ModelStatusUpdateRequest,
): Promise<ModelRegistryEntryRead> {
  return apiClient.patch(`/models/${entryId}/status`, modelRegistryEntryReadSchema, data);
}
