import { apiClient } from "@/lib/api/client";
import { pageResponseSchema, pageParamsToSearch, type PageParams, type PageResponse } from "@/lib/api/schemas/pagination";
import { jobReadSchema, type JobRead } from "@/lib/api/schemas/pipelines";

const jobPageSchema = pageResponseSchema(jobReadSchema);

export function listJobs(
  params?: PageParams & { project_id?: string },
): Promise<PageResponse<JobRead>> {
  const search = pageParamsToSearch(params);
  if (params?.project_id) search.set("project_id", params.project_id);
  return apiClient.get("/pipelines", jobPageSchema, search);
}

export function getJob(jobId: string): Promise<JobRead> {
  return apiClient.get(`/pipelines/${jobId}`, jobReadSchema);
}
