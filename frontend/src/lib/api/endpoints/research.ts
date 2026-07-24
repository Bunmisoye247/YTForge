import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import {
  researchDocumentReadSchema,
  type ResearchDocumentCreateRequest,
  type ResearchDocumentRead,
} from "@/lib/api/schemas/research";

const researchPageSchema = pageResponseSchema(researchDocumentReadSchema);

export function addResearchDocument(
  projectId: string,
  data: ResearchDocumentCreateRequest,
): Promise<ResearchDocumentRead> {
  return apiClient.post(`/projects/${projectId}/research`, researchDocumentReadSchema, data);
}

export function listResearchDocuments(
  projectId: string,
  params?: PageParams,
): Promise<PageResponse<ResearchDocumentRead>> {
  return apiClient.get(`/projects/${projectId}/research`, researchPageSchema, pageParamsToSearch(params));
}
