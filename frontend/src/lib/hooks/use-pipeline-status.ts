"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as pipelinesApi from "@/lib/api/endpoints/pipelines";
import type { StartPipelineRequest } from "@/lib/api/schemas/pipelines";
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

// Delays (ms) for a short refetch burst right after a pipeline starts. The
// steady-state polling above only engages once a fetch has actually caught
// a RUNNING job — but the workflow's first activity (which writes the
// `jobs` row) can land after our post-start invalidation already fired, and
// a fast run (dev's fakeprovider, or a real run that fails early) can start
// and finish between two 5s ticks. Without this, that window's result
// (a script that got written, a job that already failed) never reaches the
// UI until something else happens to refetch.
const START_BURST_DELAYS_MS = [1_500, 3_000, 6_000, 12_000, 20_000];

export function useStartPipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: StartPipelineRequest) => pipelinesApi.startPipeline(data),
    onSuccess: (_, variables) => {
      const projectId = variables.project_id;
      const invalidateAll = () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.pipelines.list(projectId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.scripts.list(projectId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.storyboards.detail(projectId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.assets.list(projectId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.videos.list(projectId) });
      };
      invalidateAll();
      START_BURST_DELAYS_MS.forEach((delay) => setTimeout(invalidateAll, delay));
    },
  });
}
