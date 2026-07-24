import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import { auditLogReadSchema, type AuditLogRead } from "@/lib/api/schemas/audit";

const auditLogPageSchema = pageResponseSchema(auditLogReadSchema);

export function listAuditLogs(
  entityType: string,
  entityId: string,
  params?: PageParams,
): Promise<PageResponse<AuditLogRead>> {
  const search = pageParamsToSearch(params);
  search.set("entity_type", entityType);
  search.set("entity_id", entityId);
  return apiClient.get("/audit-logs", auditLogPageSchema, search);
}
