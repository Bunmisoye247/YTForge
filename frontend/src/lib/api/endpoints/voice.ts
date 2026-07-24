import { apiClient } from "@/lib/api/client";
import { approvalReadSchema, type ApprovalRead } from "@/lib/api/schemas/approvals";
import {
  voiceoverReadSchema,
  voiceProfileReadSchema,
  type VoiceCloneRequestRequest,
  type VoiceoverCreateRequest,
  type VoiceoverRead,
  type VoiceProfileRead,
  type VoiceProfileRegisterRequest,
} from "@/lib/api/schemas/voice";
import { z } from "zod";

export function listVoiceProfiles(channelId: string): Promise<VoiceProfileRead[]> {
  return apiClient.get(`/channels/${channelId}/voice-profiles`, z.array(voiceProfileReadSchema));
}

export function listVoiceovers(projectId: string): Promise<VoiceoverRead[]> {
  return apiClient.get(`/projects/${projectId}/voiceovers`, z.array(voiceoverReadSchema));
}

export function requestVoiceClone(channelId: string, data: VoiceCloneRequestRequest): Promise<ApprovalRead> {
  return apiClient.post(`/channels/${channelId}/voice-profiles/clone-requests`, approvalReadSchema, data);
}

export function registerVoiceProfile(
  channelId: string,
  data: VoiceProfileRegisterRequest,
): Promise<VoiceProfileRead> {
  return apiClient.post(`/channels/${channelId}/voice-profiles`, voiceProfileReadSchema, data);
}

export function approveVoiceProfile(voiceProfileId: string): Promise<VoiceProfileRead> {
  return apiClient.post(`/voice-profiles/${voiceProfileId}/approve`, voiceProfileReadSchema);
}

export function addVoiceover(projectId: string, data: VoiceoverCreateRequest): Promise<VoiceoverRead> {
  return apiClient.post(`/projects/${projectId}/voiceovers`, voiceoverReadSchema, data);
}
