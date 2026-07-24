import { z } from "zod";
import { VoiceProfileStatus } from "@/types/enums";

const voiceProfileStatusSchema = z.enum([
  VoiceProfileStatus.PENDING_APPROVAL,
  VoiceProfileStatus.APPROVED,
  VoiceProfileStatus.REVOKED,
]);

export const voiceProfileReadSchema = z.object({
  id: z.string().uuid(),
  channel_id: z.string().uuid(),
  name: z.string(),
  provider: z.string(),
  provider_voice_id: z.string(),
  status: voiceProfileStatusSchema,
  consent_artifact_object_key: z.string(),
  consent_recorded_at: z.string(),
});
export type VoiceProfileRead = z.infer<typeof voiceProfileReadSchema>;

export const voiceoverReadSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  scene_id: z.string().uuid().nullable(),
  voice_profile_id: z.string().uuid().nullable(),
  asset_id: z.string().uuid(),
  transcript: z.string(),
  duration_seconds: z.string(),
  word_timestamps: z.array(z.unknown()),
});
export type VoiceoverRead = z.infer<typeof voiceoverReadSchema>;

export type VoiceCloneRequestRequest = {
  proposed_name: string;
  consent_artifact_object_key: string;
};

export type VoiceProfileRegisterRequest = {
  name: string;
  provider: string;
  provider_voice_id: string;
  consent_artifact_object_key: string;
  consent_recorded_at: string;
};

export type VoiceoverCreateRequest = {
  asset_id: string;
  transcript: string;
  duration_seconds: string;
  scene_id?: string | null;
  voice_profile_id?: string | null;
  word_timestamps?: unknown[];
};
