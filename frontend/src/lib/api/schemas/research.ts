import { z } from "zod";

export const researchDocumentReadSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  source_url: z.string(),
  title: z.string(),
  content: z.string(),
  citation: z.record(z.string(), z.unknown()),
  qdrant_point_id: z.string().nullable(),
  published_at: z.string().nullable(),
});
export type ResearchDocumentRead = z.infer<typeof researchDocumentReadSchema>;

export type ResearchDocumentCreateRequest = {
  source_url: string;
  title: string;
  content: string;
  citation?: Record<string, unknown>;
  published_at?: string | null;
};
