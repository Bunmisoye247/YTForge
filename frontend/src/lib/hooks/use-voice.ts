"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as voiceApi from "@/lib/api/endpoints/voice";
import type {
  VoiceCloneRequestRequest,
  VoiceoverCreateRequest,
  VoiceProfileRegisterRequest,
} from "@/lib/api/schemas/voice";
import { queryKeys } from "@/lib/api/query-keys";

export function useVoiceProfiles(channelId: string) {
  return useQuery({
    queryKey: queryKeys.voice.profiles(channelId),
    queryFn: () => voiceApi.listVoiceProfiles(channelId),
    enabled: Boolean(channelId),
  });
}

export function useVoiceovers(projectId: string) {
  return useQuery({
    queryKey: queryKeys.voice.voiceovers(projectId),
    queryFn: () => voiceApi.listVoiceovers(projectId),
    enabled: Boolean(projectId),
  });
}

export function useRequestVoiceClone(channelId: string) {
  return useMutation({
    mutationFn: (data: VoiceCloneRequestRequest) => voiceApi.requestVoiceClone(channelId, data),
  });
}

export function useRegisterVoiceProfile(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VoiceProfileRegisterRequest) => voiceApi.registerVoiceProfile(channelId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.voice.profiles(channelId) }),
  });
}

export function useApproveVoiceProfile(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (voiceProfileId: string) => voiceApi.approveVoiceProfile(voiceProfileId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.voice.profiles(channelId) }),
  });
}

export function useAddVoiceover(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VoiceoverCreateRequest) => voiceApi.addVoiceover(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.voice.voiceovers(projectId) }),
  });
}
