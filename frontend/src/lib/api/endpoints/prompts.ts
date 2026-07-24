import { apiClient } from "@/lib/api/client";
import {
  promptRunReadSchema,
  promptTemplateReadSchema,
  promptVersionReadSchema,
  type PromptRunCreateRequest,
  type PromptRunRead,
  type PromptTemplateRead,
  type PromptVersionCreateRequest,
  type PromptVersionRead,
} from "@/lib/api/schemas/prompts";
import { z } from "zod";

export function listPromptTemplates(): Promise<PromptTemplateRead[]> {
  return apiClient.get("/prompts/templates", z.array(promptTemplateReadSchema));
}

export function listPromptVersions(templateId: string): Promise<PromptVersionRead[]> {
  return apiClient.get(`/prompts/templates/${templateId}/versions`, z.array(promptVersionReadSchema));
}

export function createPromptVersion(data: PromptVersionCreateRequest): Promise<PromptVersionRead> {
  return apiClient.post("/prompts/versions", promptVersionReadSchema, data);
}

export function recordPromptRun(data: PromptRunCreateRequest): Promise<PromptRunRead> {
  return apiClient.post("/prompts/runs", promptRunReadSchema, data);
}
