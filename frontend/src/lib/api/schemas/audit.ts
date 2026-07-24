import { z } from "zod";

export const auditLogReadSchema = z.object({
  id: z.string().uuid(),
  actor_user_id: z.string().uuid().nullable(),
  action: z.string(),
  entity_type: z.string(),
  entity_id: z.string().uuid(),
  before: z.record(z.string(), z.unknown()).nullable(),
  after: z.record(z.string(), z.unknown()).nullable(),
  ip_address: z.string().nullable(),
});
export type AuditLogRead = z.infer<typeof auditLogReadSchema>;
