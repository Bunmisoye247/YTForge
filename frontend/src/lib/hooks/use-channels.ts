"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as channelsApi from "@/lib/api/endpoints/channels";
import type { ChannelCreateRequest, ChannelMemberAddRequest, ChannelMemberRoleUpdateRequest } from "@/lib/api/schemas/channels";
import { queryKeys } from "@/lib/api/query-keys";

export function useMyChannels() {
  return useQuery({
    queryKey: queryKeys.channels.mine,
    queryFn: channelsApi.listMyChannels,
  });
}

export function useCreateChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChannelCreateRequest) => channelsApi.createChannel(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.channels.mine }),
  });
}

export function useAddChannelMember(channelId: string) {
  return useMutation({
    mutationFn: (data: ChannelMemberAddRequest) => channelsApi.addChannelMember(channelId, data),
  });
}

export function useUpdateChannelMemberRole(channelId: string) {
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: ChannelMemberRoleUpdateRequest }) =>
      channelsApi.updateChannelMemberRole(channelId, userId, data),
  });
}
