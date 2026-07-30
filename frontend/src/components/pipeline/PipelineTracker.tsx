"use client";

import { usePipelineStatus } from "@/lib/hooks/use-pipeline-status";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Table, type Column } from "@/components/ui/Table";
import { formatDateTime, formatDuration } from "@/lib/utils/format";
import type { JobRead } from "@/lib/api/schemas/pipelines";

function durationSeconds(job: JobRead): number | null {
  if (!job.completed_at) return null;
  const start = new Date(job.started_at).getTime();
  const end = new Date(job.completed_at).getTime();
  return Number.isFinite(start) && Number.isFinite(end) ? (end - start) / 1000 : null;
}

const columns: Column<JobRead>[] = [
  {
    header: "Workflow",
    cell: (job) => (
      <div>
        <div className="font-semibold text-(--color-text) dark:text-(--color-text-dark)">{job.workflow_type}</div>
        <div className="font-mono text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
          {job.temporal_run_id.slice(0, 8)}
        </div>
      </div>
    ),
  },
  {
    header: "Started",
    cell: (job) => <span className="font-mono text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">{formatDateTime(job.started_at)}</span>,
  },
  {
    header: "Duration",
    cell: (job) => (
      <span className="font-mono text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
        {formatDuration(durationSeconds(job))}
      </span>
    ),
  },
  {
    header: "Status",
    className: "text-right",
    cell: (job) => (
      <div className="text-right">
        <StatusBadge status={job.status} />
      </div>
    ),
  },
];

export function PipelineTracker({ projectId }: { projectId?: string }) {
  const { jobs, isLoading, hasActiveJobs } = usePipelineStatus(projectId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent runs</CardTitle>
        {hasActiveJobs && (
          <span className="ml-auto font-mono text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
            polling every 5s
          </span>
        )}
      </CardHeader>
      <Table
        columns={columns}
        rows={jobs}
        rowKey={(job) => job.id}
        isLoading={isLoading}
        bordered={false}
        emptyLabel="No pipeline runs yet. These will appear once Temporal workflows are wired up (Phase 7)."
      />
    </Card>
  );
}
