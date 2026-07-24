import { z } from "zod";
import { PromptRunStatus } from "@/types/enums";

const promptRunStatusSchema = z.enum([PromptRunStatus.SUCCEEDED, PromptRunStatus.FAILED]);

export const promptTemplateReadSchema = z.object({
  id: z.string().uuid(),
  agent: z.string(),
  name: z.string(),
});
export type PromptTemplateRead = z.infer<typeof promptTemplateReadSchema>;

export const promptVersionReadSchema = z.object({
  id: z.string().uuid(),
  template_id: z.string().uuid(),
  version: z.number(),
  content: z.string(),
  front_matter: z.record(z.string(), z.unknown()),
  model_hints: z.record(z.string(), z.unknown()),
  variables: z.record(z.string(), z.unknown()),
});
export type PromptVersionRead = z.infer<typeof promptVersionReadSchema>;

export const promptRunReadSchema = z.object({
  id: z.string().uuid(),
  prompt_version_id: z.string().uuid(),
  project_id: z.string().uuid().nullable(),
  input_variables: z.record(z.string(), z.unknown()),
  rendered_prompt: z.string(),
  model_used: z.string(),
  status: promptRunStatusSchema,
  response: z.string().nullable(),
  latency_ms: z.number().nullable(),
  cost_usd: z.string().nullable(),
});
export type PromptRunRead = z.infer<typeof promptRunReadSchema>;

export type PromptVersionCreateRequest = {
  agent: string;
  name: string;
  content: string;
  front_matter?: Record<string, unknown>;
  model_hints?: Record<string, unknown>;
  variables?: Record<string, unknown>;
};

export type PromptRunCreateRequest = {
  prompt_version_id: string;
  input_variables: Record<string, unknown>;
  rendered_prompt: string;
  model_used: string;
  status: PromptRunStatus;
  project_id?: string | null;
  response?: string | null;
  latency_ms?: number | null;
  cost_usd?: string | null;
};
