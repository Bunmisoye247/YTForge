import { z } from "zod";
import { ProjectStatus } from "@/types/enums";

const projectStatusSchema = z.enum([
  ProjectStatus.IDEA,
  ProjectStatus.IN_PROGRESS,
  ProjectStatus.IN_REVIEW,
  ProjectStatus.COMPLETED,
  ProjectStatus.ARCHIVED,
]);

export const projectReadSchema = z.object({
  id: z.string().uuid(),
  channel_id: z.string().uuid(),
  trend_id: z.string().uuid().nullable(),
  created_by_user_id: z.string().uuid().nullable(),
  title: z.string(),
  status: projectStatusSchema,
  budget_usd: z.string().nullable(),
});
export type ProjectRead = z.infer<typeof projectReadSchema>;

export type ProjectCreateRequest = {
  title: string;
  trend_id?: string | null;
  budget_usd?: string | null;
};

export type ProjectUpdateRequest = {
  title?: string | null;
  budget_usd?: string | null;
};

export type ProjectStatusUpdateRequest = {
  status: ProjectStatus;
};
