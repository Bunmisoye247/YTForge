import { z } from "zod";
import { JobStatus } from "@/types/enums";

const jobStatusSchema = z.enum([
  JobStatus.RUNNING,
  JobStatus.COMPLETED,
  JobStatus.FAILED,
  JobStatus.TERMINATED,
  JobStatus.TIMED_OUT,
  JobStatus.CANCELLED,
]);

export const jobReadSchema = z.object({
  id: z.string().uuid(),
  temporal_workflow_id: z.string(),
  temporal_run_id: z.string(),
  workflow_type: z.string(),
  project_id: z.string().uuid().nullable(),
  status: jobStatusSchema,
  started_at: z.string(),
  completed_at: z.string().nullable(),
  last_heartbeat_at: z.string().nullable(),
  error: z.string().nullable(),
});
export type JobRead = z.infer<typeof jobReadSchema>;
