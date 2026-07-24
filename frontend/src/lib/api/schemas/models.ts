import { z } from "zod";
import { ModelAvailability, ModelCapability } from "@/types/enums";

const modelCapabilitySchema = z.enum([
  ModelCapability.LLM,
  ModelCapability.IMAGE,
  ModelCapability.VIDEO,
  ModelCapability.TTS,
  ModelCapability.MUSIC,
  ModelCapability.EMBEDDING,
]);

const modelAvailabilitySchema = z.enum([ModelAvailability.AVAILABLE, ModelAvailability.UNAVAILABLE]);

export const modelRegistryEntryReadSchema = z.object({
  id: z.string().uuid(),
  provider: z.string(),
  model_name: z.string(),
  capability: modelCapabilitySchema,
  status: modelAvailabilitySchema,
  discovered_at: z.string(),
  base_url: z.string().nullable(),
  last_checked_at: z.string().nullable(),
  entry_metadata: z.record(z.string(), z.unknown()),
});
export type ModelRegistryEntryRead = z.infer<typeof modelRegistryEntryReadSchema>;

export type ModelRegisterRequest = {
  provider: string;
  model_name: string;
  capability: ModelCapability;
  base_url?: string | null;
  status?: ModelAvailability;
  entry_metadata?: Record<string, unknown>;
};

export type ModelStatusUpdateRequest = {
  status: ModelAvailability;
};
