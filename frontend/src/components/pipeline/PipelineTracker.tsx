"use client";

import { usePipelineStatus } from "@/lib/hooks/use-pipeline-status";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { formatDateTime } from "@/lib/utils/format";

export function PipelineTracker({ projectId }: { projectId?: string }) {
  const { jobs, isLoading, hasActiveJobs } = usePipelineStatus(projectId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline activity</CardTitle>
        {hasActiveJobs && (
          <span className="text-xs text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
            polling every 5s
          </span>
        )}
      </CardHeader>
      {isLoading ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
      ) : jobs.length === 0 ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
          No pipeline runs yet. These will appear once Temporal workflows are wired up (Phase 7).
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {jobs.map((job) => (
            <li key={job.id} className="flex items-center justify-between text-sm">
              <div>
                <div className="font-medium text-[--color-text] dark:text-[--color-text-dark]">{job.workflow_type}</div>
                <div className="text-xs text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
                  started {formatDateTime(job.started_at)}
                </div>
              </div>
              <StatusBadge status={job.status} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
