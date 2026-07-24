import { z } from "zod";
import { StoryboardStatus } from "@/types/enums";

const storyboardStatusSchema = z.enum([
  StoryboardStatus.DRAFT,
  StoryboardStatus.READY,
  StoryboardStatus.APPROVED,
]);

export const storyboardReadSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  script_id: z.string().uuid(),
  status: storyboardStatusSchema,
});
export type StoryboardRead = z.infer<typeof storyboardReadSchema>;

export const sceneReadSchema = z.object({
  id: z.string().uuid(),
  storyboard_id: z.string().uuid(),
  sequence_index: z.number(),
  description: z.string(),
  duration_seconds: z.string(),
  image_prompt: z.string().nullable(),
  video_prompt: z.string().nullable(),
  voice_line: z.string().nullable(),
});
export type SceneRead = z.infer<typeof sceneReadSchema>;

export type StoryboardCreateRequest = {
  script_id: string;
};

export type StoryboardStatusUpdateRequest = {
  status: StoryboardStatus;
};

export type SceneCreateRequest = {
  sequence_index: number;
  description: string;
  duration_seconds: string;
  image_prompt?: string | null;
  video_prompt?: string | null;
  voice_line?: string | null;
};
