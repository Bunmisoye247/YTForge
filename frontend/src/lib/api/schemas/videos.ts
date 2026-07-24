import { z } from "zod";
import { VideoStatus } from "@/types/enums";

const videoStatusSchema = z.enum([
  VideoStatus.DRAFT,
  VideoStatus.UPLOADED,
  VideoStatus.SCHEDULED,
  VideoStatus.PUBLISHED,
  VideoStatus.FAILED,
]);

export const videoReadSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  render_asset_id: z.string().uuid(),
  title: z.string(),
  description: z.string(),
  status: videoStatusSchema,
  synthetic_content_disclosure: z.boolean(),
  youtube_video_id: z.string().nullable(),
  scheduled_publish_at: z.string().nullable(),
  published_at: z.string().nullable(),
});
export type VideoRead = z.infer<typeof videoReadSchema>;

export const seoMetadataReadSchema = z.object({
  id: z.string().uuid(),
  video_id: z.string().uuid(),
  title: z.string(),
  description: z.string(),
  thumbnail_asset_id: z.string().uuid().nullable(),
  tags: z.array(z.unknown()),
  chapters: z.array(z.unknown()),
  keywords: z.array(z.unknown()),
});
export type SeoMetadataRead = z.infer<typeof seoMetadataReadSchema>;

export type VideoCreateRequest = {
  render_asset_id: string;
  title: string;
  description: string;
  synthetic_content_disclosure?: boolean;
};

export type VideoUpdateRequest = {
  title?: string | null;
  description?: string | null;
};

export type SeoMetadataSetRequest = {
  title: string;
  description: string;
  thumbnail_asset_id?: string | null;
  tags?: unknown[];
  chapters?: unknown[];
  keywords?: unknown[];
};
