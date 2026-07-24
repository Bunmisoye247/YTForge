"use client";

import { useQuery } from "@tanstack/react-query";
import * as pipelinesApi from "@/lib/api/endpoints/pipelines";
import { queryKeys } from "@/lib/api/query-keys";
import { JobStatus } from "@/types/enums";

const ACTIVE_STATUSES: readonly string[] = [JobStatus.RUNNING];
const POLL_INTERVAL_MS = 5_000;

/**
 * Polling-backed stand-in for the live pipeline tracker. `GET /pipelines`
 * is a plain read-only endpoint today (Phase 4) — this hook's shape
 * ({ jobs, isLoading, hasActiveJobs }) is the stable contract consumers
 * use; when the events/SSE infra lands (Phase 7+), only this hook's
 * internals change; the components stay put.
 */
export function usePipelineStatus(projectId?: string) {
  const query = useQuery({
    queryKey: queryKeys.pipelines.list(projectId),
    queryFn: () => pipelinesApi.listJobs({ project_id: projectId, limit: 20 }),
    refetchInterval: (q) => {
      const jobs = q.state.data?.items ?? [];
      const hasActive = jobs.some((job) => ACTIVE_STATUSES.includes(job.status));
      return hasActive ? POLL_INTERVAL_MS : false;
    },
  });

  const jobs = query.data?.items ?? [];
  return {
    jobs,
    isLoading: query.isLoading,
    hasActiveJobs: jobs.some((job) => ACTIVE_STATUSES.includes(job.status)),
    error: query.error,
  };
}
