import { z } from "zod";
import { ChannelRole } from "@/types/enums";

const channelRoleSchema = z.enum([
  ChannelRole.OWNER,
  ChannelRole.ADMIN,
  ChannelRole.EDITOR,
  ChannelRole.VIEWER,
]);

export const channelReadSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  youtube_channel_id: z.string().nullable(),
  brand_kit: z.record(z.string(), z.unknown()),
  defaults: z.record(z.string(), z.unknown()),
});
export type ChannelRead = z.infer<typeof channelReadSchema>;

export const channelMemberReadSchema = z.object({
  id: z.string().uuid(),
  channel_id: z.string().uuid(),
  user_id: z.string().uuid(),
  role: channelRoleSchema,
});
export type ChannelMemberRead = z.infer<typeof channelMemberReadSchema>;

export type ChannelCreateRequest = {
  name: string;
  youtube_channel_id?: string | null;
  brand_kit?: Record<string, unknown>;
  defaults?: Record<string, unknown>;
};

export type ChannelMemberAddRequest = {
  user_id: string;
  role: ChannelRole;
};

export type ChannelMemberRoleUpdateRequest = {
  role: ChannelRole;
};
