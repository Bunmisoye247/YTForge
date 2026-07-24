import { apiClient } from "@/lib/api/client";
import {
  channelMemberReadSchema,
  channelReadSchema,
  type ChannelCreateRequest,
  type ChannelMemberAddRequest,
  type ChannelMemberRead,
  type ChannelMemberRoleUpdateRequest,
  type ChannelRead,
} from "@/lib/api/schemas/channels";
import { z } from "zod";

export function createChannel(data: ChannelCreateRequest): Promise<ChannelRead> {
  return apiClient.post("/channels", channelReadSchema, data);
}

export function listMyChannels(): Promise<ChannelRead[]> {
  return apiClient.get("/channels", z.array(channelReadSchema));
}

export function addChannelMember(
  channelId: string,
  data: ChannelMemberAddRequest,
): Promise<ChannelMemberRead> {
  return apiClient.post(`/channels/${channelId}/members`, channelMemberReadSchema, data);
}

export function updateChannelMemberRole(
  channelId: string,
  userId: string,
  data: ChannelMemberRoleUpdateRequest,
): Promise<ChannelMemberRead> {
  return apiClient.patch(`/channels/${channelId}/members/${userId}`, channelMemberReadSchema, data);
}
