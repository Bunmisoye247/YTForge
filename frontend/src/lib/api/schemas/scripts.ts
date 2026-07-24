import { z } from "zod";
import { FactCheckVerdict, ScriptStatus } from "@/types/enums";

const scriptStatusSchema = z.enum([
  ScriptStatus.DRAFT,
  ScriptStatus.IN_REVIEW,
  ScriptStatus.APPROVED,
  ScriptStatus.REJECTED,
]);

const factCheckVerdictSchema = z.enum([FactCheckVerdict.PASSED, FactCheckVerdict.FLAGGED]);

export const scriptReadSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  version: z.number(),
  status: scriptStatusSchema,
  sections: z.record(z.string(), z.unknown()),
  model_used: z.string().nullable(),
  token_count: z.number().nullable(),
});
export type ScriptRead = z.infer<typeof scriptReadSchema>;

export const factCheckReadSchema = z.object({
  id: z.string().uuid(),
  script_id: z.string().uuid(),
  script_version: z.number(),
  verdict: factCheckVerdictSchema,
  flags: z.array(z.unknown()),
  model_used: z.string().nullable(),
});
export type FactCheckRead = z.infer<typeof factCheckReadSchema>;

export type ScriptCreateRequest = {
  sections?: Record<string, unknown>;
  model_used?: string | null;
  token_count?: number | null;
};

export type ScriptStatusUpdateRequest = {
  status: ScriptStatus;
};

export type FactCheckCreateRequest = {
  verdict: FactCheckVerdict;
  flags?: unknown[];
  model_used?: string | null;
};
