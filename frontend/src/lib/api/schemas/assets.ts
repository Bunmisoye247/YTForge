import { z } from "zod";
import { AssetStatus, AssetType } from "@/types/enums";

const assetTypeSchema = z.enum([
  AssetType.IMAGE,
  AssetType.CLIP,
  AssetType.AUDIO,
  AssetType.MUSIC,
  AssetType.THUMBNAIL,
  AssetType.RENDER,
]);

const assetStatusSchema = z.enum([
  AssetStatus.PENDING,
  AssetStatus.READY,
  AssetStatus.FAILED,
  AssetStatus.ORPHANED,
]);

export const assetReadSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  scene_id: z.string().uuid().nullable(),
  asset_type: assetTypeSchema,
  status: assetStatusSchema,
  bucket: z.string(),
  object_key: z.string(),
  checksum_sha256: z.string().nullable(),
  provenance: z.record(z.string(), z.unknown()),
});
export type AssetRead = z.infer<typeof assetReadSchema>;

export type AssetRegisterRequest = {
  asset_type: AssetType;
  bucket: string;
  object_key: string;
  scene_id?: string | null;
  checksum_sha256?: string | null;
  provenance?: Record<string, unknown>;
};

export const presignedUrlReadSchema = z.object({ url: z.string() });
export type PresignedUrlRead = z.infer<typeof presignedUrlReadSchema>;

export type ImageGenerateRequest = {
  prompt: string;
  negative_prompt?: string | null;
  width?: number;
  height?: number;
};
